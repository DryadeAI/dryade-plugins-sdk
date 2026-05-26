"""Internal-reference leak guard — CI gate for the public SDK repo.

Scans ALL author-visible files (Python source, the JSON schema, CI workflow
YAML, every markdown doc, llms.txt) for tokens that belong only to the private
Dryade monorepo: internal governance IDs, internal file/module paths, and
descriptions of how the platform enforces plugin security.

A public reader of this repo must be able to author plugins without learning
the internal phase plan, the closed-source module layout, or the runtime
security-enforcement mechanics. This test fails the build if any such token
appears. It is intentionally broad — see the prior narrow guard that let a
release ship with phase IDs in docstrings and the schema.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories that never ship to authors.
_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build", ".mypy_cache"}
# This guard file legitimately *names* the forbidden tokens in its own pattern
# table; exclude it (and nothing else) from the scan.
_SELF = Path(__file__).name


def _scanned_files() -> list[Path]:
    out: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path.name == _SELF:
            continue
        if path.suffix in {".py", ".json", ".yml", ".yaml", ".md", ".j2"} or path.name == "llms.txt":
            out.append(path)
    return sorted(out)


SCANNED = _scanned_files()

# Forbidden patterns. Each is something a public plugin author has no business
# seeing. Grouped by what they leak.
FORBIDDEN: dict[str, str] = {
    # --- internal governance IDs ---
    "internal phase id": r"\bPhase \d{2,4}\b|\b339-0\d[ab]?\b",
    "internal task id": r"\bT-\d{2,4}(?:-\d+){0,2}[ab]?(?:-\d+)?\b|\bT-09-\d\b",
    "internal decision id": r"\bD-\d{2}\b",
    "internal finding id": r"\bF\d(?:\.\d+)?\b",
    "internal rule ref": r"Rule\s+§\d+",
    "governance doc name": r"CLAUDE\.md",
    # --- closed-source module / file paths ---
    "core ee module": r"core[./]ee|plugins_ee|plugin_security",
    "core adapters path": r"core/core/adapters",
    "rust pm internals": r"scanner\.rs|dryade-plugin-manager",
    "internal scripts": r"sign_plugins\.py|lint_plugins\.py",
    "internal monorepo path": r"dryade-internal|/home/dryade|\.planning/",
    # --- runtime / security-enforcement mechanics ---
    "dryade-pm dev cmd": r"dryade-pm\s+push",
    "runtime entrypoint": r"gunicorn|core\.api\.main",
    "tofu / pq forge": r"\bTOFU\b|ML-DSA",
    "allowlist internals": r"allowlist\.enc|allowed-plugins\.json|pm\.sock|pm-lifecycle\.sock|SO_PEERCRED",
    "internal ports": r"\bport 947[12]\b|\b947[12]\b",
    "internal signer modules": r"tier-config\.ts|license-signer\.ts|approve-plugin/index\.ts",
    "internal hash symbol": r"_compute_plugin_hash_pair",
    # --- lab infra ---
    "internal IP literal": r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
    "internal hostname": r"\bdryade-thor\b|\bjetson-thor\b",
    "internal codename": r"\blovable\b",
}


@pytest.mark.parametrize("f", SCANNED, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_internal_leaks(f: Path) -> None:
    """Every author-visible file must be free of internal references."""
    content = f.read_text(encoding="utf-8", errors="ignore")
    rel = f.relative_to(REPO_ROOT)
    violations: list[str] = []
    for name, pattern in FORBIDDEN.items():
        matches = re.findall(pattern, content)
        if matches:
            violations.append(f"{name}: {sorted(set(matches))[:5]}")
    assert not violations, f"{rel} leaks internal references:\n  " + "\n  ".join(violations)


def test_marketing_drafts_not_in_repo() -> None:
    """`.private/` and `MARKETING.md` must never land in the public repo."""
    forbidden = [REPO_ROOT / ".private", REPO_ROOT / "MARKETING.md"]
    leaks = [p for p in forbidden if p.exists()]
    assert not leaks, f"Internal-only drafts leaked into public repo: {leaks}"


def test_scan_found_expected_files() -> None:
    """Sanity — the scan reaches source, schema, CI, and docs."""
    names = {str(p.relative_to(REPO_ROOT)) for p in SCANNED}
    for expected in (
        "src/dryade_plugins_sdk/__init__.py",
        "src/dryade_plugins_sdk/_schemas/dryade-manifest-v2.schema.json",
        ".github/workflows/ci.yml",
        "README.md",
    ):
        assert expected in names, f"leak scan is not reaching {expected}"
