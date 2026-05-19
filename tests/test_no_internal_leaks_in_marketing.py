"""Brand-leak regression net — fails CI if public markdown contains internal references.

T-09-1 mitigation: greps every public-facing markdown file for forbidden
patterns (internal monorepo paths, internal phase numbers, internal IP
addresses, internal codenames). CI gate — a failing run blocks the merge.

Scoped to files that ship to the public repo. The `.private/` directory and
`MARKETING.md` (launch-content drafts) live in the internal monorepo or an
ops drive and never appear in this tree — `.gitignore` enforces that and
`test_marketing_drafts_not_in_repo` asserts it as well.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _public_markdown_files() -> list[Path]:
    """Files that get crawled / read by external eyes — must be leak-free."""
    candidates: list[Path] = []
    candidates.extend(REPO_ROOT.glob("*.md"))
    candidates.extend((REPO_ROOT / "docs").glob("*.md") if (REPO_ROOT / "docs").exists() else [])
    candidates.extend((REPO_ROOT / "examples").glob("*.md"))
    candidates.extend((REPO_ROOT / "examples").glob("*/README.md"))
    candidates.extend((REPO_ROOT / ".github").glob("PULL_REQUEST_TEMPLATE.md"))
    candidates.extend((REPO_ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml"))
    candidates.extend((REPO_ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.md"))
    candidates.extend((REPO_ROOT / ".demo").glob("*.md"))
    # llms.txt is also public-facing
    llms = REPO_ROOT / "llms.txt"
    if llms.exists():
        candidates.append(llms)
    return sorted(set(candidates))


PUBLIC_MARKDOWN = _public_markdown_files()


# Files allowed to mention phase numbers (changelog can reference historical work).
PHASE_NUMBER_ALLOWLIST = {"CHANGELOG.md", "docs/changelog.md"}

FORBIDDEN_PATTERNS: dict[str, str] = {
    "internal monorepo path": r"dryade-internal|/home/dryade",
    "planning dir leak": r"\.planning/",
    "internal phase number": r"\bPhase \d{2,4}\b",
    "internal IP literal": r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
    "internal codename": r"\blovable\b",
    "internal hostname": r"\bdryade-thor\b|\bjetson-thor\b",
    "placeholder discord url": r"DISCORD_URL_PLACEHOLDER|\{\{DISCORD_URL\}\}",
}


@pytest.mark.parametrize(
    "md_file",
    PUBLIC_MARKDOWN,
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_no_internal_leaks(md_file: Path) -> None:
    """Every public-facing markdown file must be free of internal references."""
    content = md_file.read_text(encoding="utf-8")
    rel = md_file.relative_to(REPO_ROOT)
    violations: list[str] = []

    for name, pattern in FORBIDDEN_PATTERNS.items():
        if name == "internal phase number" and str(rel) in PHASE_NUMBER_ALLOWLIST:
            continue
        matches = re.findall(pattern, content)
        if matches:
            violations.append(f"{name}: {matches[:3]}")

    assert not violations, f"{rel} contains internal leaks: {violations}"


def test_marketing_drafts_not_in_repo() -> None:
    """`.private/` and `MARKETING.md` must NEVER land in this public repo."""
    forbidden_paths = [
        REPO_ROOT / ".private",
        REPO_ROOT / "MARKETING.md",
    ]
    leaks = [p for p in forbidden_paths if p.exists()]
    assert not leaks, (
        f"Marketing-drafts leak — these files must live in the internal monorepo "
        f"or an ops drive, not in the public SDK repo: {leaks}"
    )


def test_at_least_one_public_markdown_found() -> None:
    """Sanity check — the test discovers at least the four root .md files."""
    must_have = {"README.md", "CHANGELOG.md", "SECURITY.md", "CONTRIBUTING.md"}
    found_names = {p.name for p in PUBLIC_MARKDOWN}
    missing = must_have - found_names
    assert not missing, (
        f"Brand-leak test cannot find these expected public files: {missing}. "
        "Either the files moved or the discovery glob is broken."
    )
