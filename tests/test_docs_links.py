"""Verify markdown links in `Dryade/docs/plugins.md` and sub-pages resolve.

The canonical plugin author landing is `Dryade/docs/plugins.md` (lowercase,
case-collision-safe per H9). This test walks the landing page and the six
sub-pages, parses every relative markdown link, and asserts the target file
exists on disk. Anchor (`#section`) and HTTP/mailto links are skipped.

A top-level `test_no_uppercase_plugins_md` guards against any future
`Dryade/docs/PLUGINS.md` (uppercase) being created alongside the lowercase
canonical file — that would silently collide on case-insensitive filesystems
(macOS default, Windows).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "Dryade" / "docs"

# Files to scan (relative to DOCS_ROOT). H9 fix: lowercase plugins.md only.
SCANNED_FILES = [
    "plugins.md",  # canonical landing (lowercase — H9)
    "plugins/manifest.md",
    "plugins/agents.md",
    "plugins/tools.md",
    "plugins/routes.md",
    "plugins/signing.md",
    "plugins/tiers.md",
    "community/PLUGIN-DEVELOPER-GUIDE.md",
]


def test_no_uppercase_plugins_md() -> None:
    """H9 fix — no `PLUGINS.md` (uppercase) exists alongside `plugins.md`."""
    upper = DOCS_ROOT / "PLUGINS.md"
    assert not upper.exists(), (
        "H9 violation: Dryade/docs/PLUGINS.md exists alongside plugins.md. "
        "Case-insensitive filesystems (macOS, Windows) collide these two. "
        "Use only the lowercase canonical landing."
    )


@pytest.mark.parametrize("doc_path", SCANNED_FILES)
def test_internal_links_resolve(doc_path: str) -> None:
    """Every relative markdown link in a doc must resolve to an existing file."""
    full_path = DOCS_ROOT / doc_path
    if not full_path.exists():
        pytest.skip(f"{doc_path} not present yet (Task may not have landed)")
    text = full_path.read_text()
    # Find markdown links: [text](path) where path is not http/https/mailto
    links = re.findall(r"\]\(([^)]+)\)", text)
    broken: list[str] = []
    for link in links:
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Resolve relative to the doc's directory
        link_path = link.split("#")[0]  # strip anchors
        if not link_path:
            continue
        target = (full_path.parent / link_path).resolve()
        if not target.exists():
            broken.append(f"{doc_path}: {link} -> {target}")
    assert not broken, f"Broken links: {broken}"
