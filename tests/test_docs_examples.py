"""Verify JSON manifest examples in docs validate against v2 schema, and
no internal leaks / non-existent CLI references / community-tier mentions
appear.

This is the regression net for the BREAKER findings closed in Phase 339-05:

- F5.1: every fenced ```json``` manifest example in `Dryade/docs/plugins/*.md`
  must validate against `dryade-manifest-v2.schema.json`.
- F5.4: no doc references `dryade create-plugin`, `dryade validate-plugin`,
  `dryade plugins list`, or `dryade restart` (commands that don't exist).
- T-339-05-04 (Rule §11): no doc shows `required_tier: "community"` as a
  valid manifest value.
- T-339-05-01: no doc leaks repo-internal paths, PM internals, or private
  network addresses.
- H6: signing.md disambiguates author single-sig (Ed25519) from marketplace
  dual-sign (Ed25519 + ML-DSA-65 server-side, out of SDK scope).

Tests are scoped to the docs tree. They run from the internal monorepo
today; when the SDK splits out (339-08), this file may need a fixture that
vendors the docs OR an env-var pointing at the source-of-truth.
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


# Doc files that must NOT contain F5.4 ghost commands.
# H9 fix: lowercase plugins.md only.
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


def _plugin_author_docs() -> list[Path]:
    """Just the plugin-author landing + sub-pages + the community redirect stub.

    The internal-leak ban is scoped to the docs Phase 339-05 owns. Operator
    docs (KNOWN_LIMITATIONS, SECURITY_MODEL, HARDENING, deployment) are
    PUBLIC architecture references — they intentionally document the
    ~/.dryade/pm-pubkey.pem TOFU pin and the localhost:9471 PM-to-core
    transport because those are architecture facts, not author concerns.
    Author docs MUST NOT redirect new authors toward those internals.
    """
    paths = [
        DOCS_ROOT / "plugins.md",
        DOCS_ROOT / "plugins" / "manifest.md",
        DOCS_ROOT / "plugins" / "agents.md",
        DOCS_ROOT / "plugins" / "tools.md",
        DOCS_ROOT / "plugins" / "routes.md",
        DOCS_ROOT / "plugins" / "signing.md",
        DOCS_ROOT / "plugins" / "tiers.md",
        DOCS_ROOT / "community" / "PLUGIN-DEVELOPER-GUIDE.md",
    ]
    return [p for p in paths if p.exists()]


def test_manifest_examples_validate() -> None:
    """F5.1 regression net — every JSON manifest example validates."""
    if not SCHEMA_PATH.exists():
        pytest.skip("v2 schema not present (339-02 not landed)")
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
    """F5.4 regression net — no doc references non-existent CLI commands.

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


def test_no_internal_leaks() -> None:
    """Plugin-author docs must not leak internal repo paths or PM internals.

    Forbidden leak surface (banned in author docs):
      - /home/dryade absolute paths
      - dryade-internal repo references
      - ~/.dryade/pm-pubkey.pem TOFU pin path
      - ~/.dryade/allowlist.enc encrypted allowlist path
      - ~/.dryade/pm.sock UDS lifecycle channel
      - 192.168.x.x lab IPs
      - port 9471 PM-to-core HTTP transport
      - _shared/tier-config.ts / license-signer.ts internal modules
      - ML-DSA-65 forge mechanics (algorithm name OK; forge detail NOT)

    Scope: this rule binds the plugin-author landing page + sub-pages + the
    community redirect stub. Operator-facing docs (SECURITY_MODEL,
    KNOWN_LIMITATIONS, HARDENING, deployment) intentionally document
    architecture facts like the TOFU pubkey pin and the PM-to-core
    localhost:9471 transport — those are public architecture, not author
    concerns. Author docs MUST NOT redirect authors toward those internals.
    """
    forbidden_patterns = [
        r"/home/dryade",
        r"\bdryade-internal\b",
        r"~/\.dryade/pm-pubkey\.pem",
        r"~/\.dryade/allowlist\.enc",
        r"~/\.dryade/pm\.sock",
        r"\b192\.168\.",
        r"\bport 9471\b",
        r"_shared/tier-config\.ts",
        r"_shared/license-signer\.ts",
        r"ML-DSA-65 forge",
    ]
    hits: list[str] = []
    for doc in _plugin_author_docs():
        text = doc.read_text()
        for pat in forbidden_patterns:
            if re.search(pat, text):
                hits.append(f"{doc.relative_to(REPO_ROOT)}: {pat}")
    assert not hits, f"Internal leaks in author docs: {hits}"


def test_no_community_required_tier() -> None:
    """Rule §11 — no doc shows `required_tier: "community"` as a valid value."""
    hits: list[str] = []
    for doc in _all_docs():
        text = doc.read_text()
        for block in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
            if '"required_tier": "community"' in block or '"required_tier":"community"' in block:
                hits.append(str(doc.relative_to(REPO_ROOT)))
    assert not hits, f"Rule §11 violation in: {hits}"


def test_canonical_landing_exists() -> None:
    """Sanity — Dryade/docs/plugins.md must exist (H9: lowercase only)."""
    assert (DOCS_ROOT / "plugins.md").exists()
    # H9: no uppercase variant
    assert not (DOCS_ROOT / "PLUGINS.md").exists(), (
        "H9 violation: uppercase PLUGINS.md exists alongside lowercase plugins.md"
    )


def test_signing_doc_disambiguates_author_vs_marketplace() -> None:
    """H6 regression net — signing.md distinguishes author from marketplace.

    `signing.md` must:
    1. Call out the author signature as a SINGLE Ed25519 signature.
    2. Call out the marketplace dual-sign (Ed25519 + ML-DSA-65) as
       server-side / out of SDK scope.
    3. Explicitly scope the marketplace re-signing OUT.
    """
    signing = DOCS_ROOT / "plugins" / "signing.md"
    if not signing.exists():
        pytest.skip("signing.md not present")
    text = signing.read_text()
    # Must mention author single-signature explicitly
    assert re.search(r"single.?signature|single-sig", text, re.IGNORECASE), (
        "H6: signing.md must call out author Ed25519 as a SINGLE signature"
    )
    # Must mention marketplace's role as dual-sign / server-side
    assert re.search(
        r"marketplace.+dual|dual.+marketplace|"
        r"marketplace.+server-side|server-side.+key",
        text,
        re.IGNORECASE,
    ), "H6: signing.md must call out marketplace dual-sign / server-side Ed25519 + ML-DSA-65"
    # Must mention "out of SDK scope" or equivalent
    assert re.search(r"out of (SDK )?scope", text, re.IGNORECASE), (
        "H6: marketplace signing must be scoped out explicitly"
    )
