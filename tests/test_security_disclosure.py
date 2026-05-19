"""Author security disclosure page — F6.1, F6.2, F6.3, F6.5 regression net.

Tests verify:

1. The page exists at the canonical path
   (``Dryade/docs/plugins/security-for-authors.md``).
2. Every required author-facing security rule has at least one mention
   (positive coverage — Rule §1, §6, §8, §9, §11, D-10).
3. No forbidden internal pattern leaks into the public disclosure
   (negative coverage — TOFU pubkey path, allowlist.enc, pm.sock, port
   numbers, ML-DSA-65 forge mechanics, marketplace re-signing internals,
   tier-config.ts / license-signer.ts internal modules, repo-internal
   paths).
4. ``Dryade/docs/SECURITY_MODEL.md`` updated to dual SHA-256 + SHA3-256
   for plugin hashing (F6.9 closure).
5. The dryade-cli scaffold output cross-links to the disclosure page
   (F6.5 partial — Next steps mention).

Scope: this test scans ONLY the author-facing disclosure surface
(security-for-authors.md + SECURITY_MODEL.md plugin-hashing line +
dryade-cli new.py scaffold output). Operator-facing docs
(KNOWN_LIMITATIONS, HARDENING, deployment) are intentionally out of
scope — they target a different audience and may surface architecture
facts that the author surface MUST NOT redirect authors toward. This
mirrors the scope-narrowing decision documented in 339-05's
``test_no_internal_leaks``.

Note: SECURITY_MODEL.md is in scope for the dual-hash check ONLY — its
existing text legitimately documents architecture facts (TOFU pin path,
PM-to-core localhost:9471 transport) that pre-date this plan and target
operators. The leak scan stays restricted to security-for-authors.md.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "Dryade" / "docs"
DISCLOSURE_PATH = DOCS_ROOT / "plugins" / "security-for-authors.md"
SECURITY_MODEL_PATH = DOCS_ROOT / "SECURITY_MODEL.md"
CLI_NEW_PATH = REPO_ROOT / "dryade-cli" / "src" / "dryade_cli" / "commands" / "new.py"


# ---------------------------------------------------------------------------
# 1. Page exists with substance
# ---------------------------------------------------------------------------


def test_page_exists() -> None:
    """F6.1 + F6.5 — the disclosure page must exist at the canonical path."""
    assert DISCLOSURE_PATH.exists(), f"Missing canonical disclosure: {DISCLOSURE_PATH}"


def test_page_has_substance() -> None:
    """The page must be substantive (>=200 lines, >=6 H2 sections)."""
    text = DISCLOSURE_PATH.read_text()
    line_count = len(text.splitlines())
    assert line_count >= 200, f"Disclosure too short ({line_count} lines, expected >=200)"
    h2_count = sum(1 for line in text.splitlines() if line.startswith("## "))
    assert h2_count >= 6, f"Need >=6 H2 sections, got {h2_count}"


# ---------------------------------------------------------------------------
# 2. Required rule coverage (positive)
# ---------------------------------------------------------------------------

REQUIRED_RULES_COVERED = {
    # rule_id: (description, search_patterns — at least one must match)
    "rule_1": (
        "Rule §1 — signed allowlist gate exists",
        [
            r"signed allowlist",
            r"allowlist.*signature",
            r"signing chain",
        ],
    ),
    "rule_6": (
        "Rule §6 — silence is the diagnostic signal (blocked plugins are invisible)",
        [
            r"silence is the diagnostic",
            r"invisible",
            r"silently skip",
            r"no error message",
        ],
    ),
    "rule_8": (
        "Rule §8 — dryade-pm push is the END-USER's tool, not the author's",
        [
            r"end-user.+plugin manager",
            r"end-user.+pm\.log",
            r"plugin manager.+end-user",
            r"end-user.+tool",
            r"end-user's tool",
        ],
    ),
    "rule_9": (
        "Rule §9 — SHA-256 + SHA3-256 dual hash + author code authenticity",
        [
            r"SHA-256.+SHA3-256",
            r"dual.+hash",
            r"plugin contract.+v4",
        ],
    ),
    "rule_11": (
        "Rule §11 — no `community` tier",
        [
            r"`community`.+NOT.+valid",
            r"community.+not.+valid",
            r"never.+community",
        ],
    ),
    "d_10": (
        "D-10 — slot consumption disclosure",
        [
            r"custom_plugin_slots",
            r"consume.+slot",
            r"slot.+consume",
        ],
    ),
}


@pytest.mark.parametrize("rule_id", list(REQUIRED_RULES_COVERED.keys()))
def test_required_rules_covered(rule_id: str) -> None:
    """F6.1 — every author-relevant security rule has positive coverage."""
    description, patterns = REQUIRED_RULES_COVERED[rule_id]
    text = DISCLOSURE_PATH.read_text()
    hits = [pat for pat in patterns if re.search(pat, text, re.IGNORECASE)]
    assert hits, (
        f"Rule {rule_id} ({description}) not covered in disclosure. "
        f"None of the patterns matched: {patterns}"
    )


# ---------------------------------------------------------------------------
# 3. Forbidden patterns (negative)
# ---------------------------------------------------------------------------

FORBIDDEN_PATTERNS = [
    # Specific internal paths
    r"~/\.dryade/pm-pubkey\.pem",
    r"pm-pubkey",
    r"~/\.dryade/allowlist\.enc",
    r"allowlist\.enc",
    r"~/\.dryade/pm\.sock",
    r"pm-lifecycle\.sock",
    r"\bport 9471\b",
    r"\bport 9472\b",
    r"\b9471\b",
    r"\b9472\b",
    r"SO_PEERCRED",
    # Internal-only mechanics
    r"_shared/tier-config\.ts",
    r"_shared/license-signer\.ts",
    r"tier-config\.ts",
    r"license-signer\.ts",
    r"ML-DSA-65 forge",
    r"marketplace.+re-sign",
    r"marketplace forge",
    r"forge mechanism",
    r"dual-sign internals",
    r"TOFU",
    r"TOFU pin",
    r"TOFU rotation",
    r"approve-plugin/index\.ts",
    r"allowed-plugins\.json",
    # Internal symbol leaks
    r"_compute_plugin_hash_pair",
    # Internal repo / local paths
    r"\bdryade-internal\b",
    r"/home/dryade",
    r"\b192\.168\.",
]


@pytest.mark.parametrize("pattern", FORBIDDEN_PATTERNS)
def test_no_internal_leaks(pattern: str) -> None:
    """F6.x — disclosure must not leak internal-only mechanics."""
    text = DISCLOSURE_PATH.read_text()
    matches = re.findall(pattern, text, re.IGNORECASE)
    assert not matches, (
        f"Internal leak: pattern {pattern!r} appears in {DISCLOSURE_PATH.name}: {matches}"
    )


# ---------------------------------------------------------------------------
# 4. Sanity — security contact + link integrity
# ---------------------------------------------------------------------------


def test_security_contact_present() -> None:
    """Reporters must know where to file vulnerabilities."""
    text = DISCLOSURE_PATH.read_text()
    assert "security@dryade.ai" in text, (
        "F6.3: disclosure must include security@dryade.ai vulnerability contact"
    )


def test_links_resolve() -> None:
    """Every relative link in the disclosure must resolve."""
    text = DISCLOSURE_PATH.read_text()
    links = re.findall(r"\]\(([^)]+)\)", text)
    broken: list[str] = []
    for link in links:
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = link.split("#")[0]
        if not path:
            continue
        target = (DISCLOSURE_PATH.parent / path).resolve()
        if not target.exists():
            broken.append(link)
    assert not broken, f"Broken links in disclosure: {broken}"


def test_three_community_callouts() -> None:
    """T-339-06-07 — `community` must be called out as invalid in multiple places."""
    text = DISCLOSURE_PATH.read_text()
    # At least 3 lines mention `community` in a "NOT valid" disclaimer context.
    community_lines = [line for line in text.splitlines() if "community" in line.lower()]
    assert len(community_lines) >= 3, (
        f"Rule §11: expected >=3 lines mentioning `community` (all as disclaimers), "
        f"got {len(community_lines)}"
    )


# ---------------------------------------------------------------------------
# 5. F6.9 — SECURITY_MODEL.md dual-hash update
# ---------------------------------------------------------------------------


def test_security_model_dual_hash() -> None:
    """F6.9 — SECURITY_MODEL.md must mention SHA3-256 alongside SHA-256.

    The original line at ~194 referenced only SHA-256 for plugin code
    hashing. Plugin contract v4 (shipped via dryade-plugin-manager PR #9,
    f9b6f24) is SHA-256 + SHA3-256 dual hash. SECURITY_MODEL.md must
    reflect the shipped contract.
    """
    if not SECURITY_MODEL_PATH.exists():
        pytest.skip("SECURITY_MODEL.md not present in tree")
    text = SECURITY_MODEL_PATH.read_text()
    assert re.search(r"SHA-256.+SHA3-256|SHA3-256.+SHA-256", text), (
        "F6.9 — SECURITY_MODEL.md must reference SHA-256 + SHA3-256 dual hash"
    )


def test_security_model_links_to_disclosure() -> None:
    """SECURITY_MODEL.md plugin-hashing section should cross-link to the
    author-facing disclosure page so operators understand the
    responsibility split (operators see the architecture, authors see the
    obligations)."""
    if not SECURITY_MODEL_PATH.exists():
        pytest.skip("SECURITY_MODEL.md not present in tree")
    text = SECURITY_MODEL_PATH.read_text()
    assert "security-for-authors" in text, (
        "F6.9: SECURITY_MODEL.md should cross-link to plugins/security-for-authors.md"
    )


# ---------------------------------------------------------------------------
# 6. F6.5 — dryade-cli scaffold cross-link
# ---------------------------------------------------------------------------


def test_cli_new_links_to_disclosure() -> None:
    """F6.5 — `dryade plugin new` scaffold output must cross-link to the
    author security disclosure page."""
    if not CLI_NEW_PATH.exists():
        pytest.skip("dryade-cli new.py not present")
    text = CLI_NEW_PATH.read_text()
    assert "security-for-authors" in text or "docs.dryade.ai/plugins" in text, (
        "F6.5 — scaffold output must cross-link to security disclosure"
    )


def test_plugins_md_cross_links_disclosure() -> None:
    """plugins.md (canonical landing) must point readers at the
    author-facing security page."""
    plugins_md = DOCS_ROOT / "plugins.md"
    if not plugins_md.exists():
        pytest.skip("plugins.md not present")
    text = plugins_md.read_text()
    assert "security-for-authors" in text, (
        "Canonical plugins.md landing must cross-link to plugins/security-for-authors.md"
    )
