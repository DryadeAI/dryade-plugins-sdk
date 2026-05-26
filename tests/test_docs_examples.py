"""Verify JSON manifest examples in docs validate against the v2 schema and
reference only commands that exist / no community-tier mentions.

This is the docs-example execution net:

- every fenced ```json``` manifest example in the docs tree must validate
  against `dryade-manifest-v2.schema.json`.
- no doc references `dryade create-plugin`, `dryade validate-plugin`,
  `dryade plugins list`, or `dryade restart` (commands that don't exist).
- no doc shows `required_tier: "community"` as a valid manifest value.

Internal-reference leak detection is handled by `tests/test_no_internal_leaks.py`.
These tests are scoped to the docs tree when one is present alongside the
source; otherwise they skip.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "Dryade" / "docs"
SCHEMA_PATH = REPO_ROOT / "dryade-plugins" / "schemas" / "dryade-manifest-v2.schema.json"


# Doc files that must NOT contain non-existent (ghost) CLI commands.
DOCS_WITH_LIVE_CLI_REFS = [
    "plugins.md",
    "plugins/manifest.md",
    "plugins/agents.md",
    "plugins/tools.md",
    "plugins/routes.md",
    "plugins/signing.md",
    "plugins/tiers.md",
    "community/PLUGIN-DEVELOPER-GUIDE.md",
]


def _all_docs() -> list[Path]:
    """All markdown files under Dryade/docs/ except the archive."""
    if not DOCS_ROOT.exists():
        return []
    return [p for p in DOCS_ROOT.rglob("*.md") if "_archive" not in str(p)]


def test_manifest_examples_validate() -> None:
    """Every JSON manifest example in the docs validates against the schema."""
    if not SCHEMA_PATH.exists():
        pytest.skip("v2 schema not present alongside the docs tree")
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema)
    failures: list[str] = []
    for doc in _all_docs():
        text = doc.read_text()
        for block in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
            try:
                m = json.loads(block)
            except json.JSONDecodeError:
                continue
            # Only validate blocks that look like manifests
            if not isinstance(m, dict) or "manifest_version" not in m:
                continue
            # Skip placeholder strings like "<populated by `dryade plugin package`>"
            if "<" in block and ">" in block:
                m = {k: v for k, v in m.items() if not (isinstance(v, str) and v.startswith("<"))}
            errors = list(validator.iter_errors(m))
            if errors:
                failures.append(f"{doc.relative_to(REPO_ROOT)}: {errors[0].message}")
    assert not failures, f"Manifest example failures: {failures}"


@pytest.mark.parametrize("doc_path", DOCS_WITH_LIVE_CLI_REFS)
def test_only_existing_cli_commands(doc_path: str) -> None:
    """No doc references non-existent CLI commands.

    Forbidden: `dryade create-plugin`, `dryade validate-plugin`,
    `dryade restart`, `dryade plugins list`. Author CLI is
    `dryade plugin <verb>`.
    """
    full = DOCS_ROOT / doc_path
    if not full.exists():
        pytest.skip(f"{doc_path} not present")
    text = full.read_text()
    forbidden = [
        r"\bdryade create-plugin\b",
        r"\bdryade validate-plugin\b",
        r"\bdryade restart\b",
        r"\bdryade plugins list\b",
    ]
    hits = []
    for pat in forbidden:
        if re.search(pat, text):
            hits.append(pat)
    assert not hits, f"{doc_path} contains non-existent CLI references: {hits}"


def test_no_community_required_tier() -> None:
    """No doc shows `required_tier: "community"` as a valid value."""
    hits: list[str] = []
    for doc in _all_docs():
        text = doc.read_text()
        for block in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
            if '"required_tier": "community"' in block or '"required_tier":"community"' in block:
                hits.append(str(doc.relative_to(REPO_ROOT)))
    assert not hits, f"community-tier example found in: {hits}"


def test_canonical_landing_exists() -> None:
    """Sanity — when a docs tree is present, the landing page is lowercase only."""
    if not (DOCS_ROOT / "plugins.md").exists():
        pytest.skip("docs tree not present alongside the source")
    assert not (DOCS_ROOT / "PLUGINS.md").exists(), (
        "uppercase PLUGINS.md exists alongside lowercase plugins.md"
    )
