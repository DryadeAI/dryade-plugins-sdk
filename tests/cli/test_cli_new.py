"""Scaffold (`dryade plugin new`) regression net.

- Scaffold output must validate against the v2 schema.
- Scaffolded tests must be meaningful (not pass-no-op).
- The scaffold path must be discoverable from `dryade plugin new --help`.
- `--tier community` must be rejected.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from dryade_plugins_sdk.cli.cli import app


def test_scaffold_creates_dir(scaffolded_plugin: Path):
    """Scaffolded directory contains the canonical files."""
    assert scaffolded_plugin.is_dir()
    assert (scaffolded_plugin / "dryade.json").exists()
    assert (scaffolded_plugin / "__init__.py").exists()
    assert (scaffolded_plugin / "plugin.py").exists()
    assert (scaffolded_plugin / "pyproject.toml").exists()
    assert (scaffolded_plugin / "README.md").exists()
    assert (scaffolded_plugin / ".gitignore").exists()
    assert (scaffolded_plugin / "tests" / "test_plugin.py").exists()


def test_scaffold_manifest_is_v2(scaffolded_plugin: Path):
    """manifest_version must be exactly '2.0' and carry no entry_point."""
    manifest = json.loads((scaffolded_plugin / "dryade.json").read_text())
    assert manifest["manifest_version"] == "2.0"
    assert "entry_point" not in manifest, "v2 manifests must not carry entry_point"
    assert manifest["required_tier"] == "starter"
    assert manifest["name"] == "test_plugin"


def test_scaffold_tests_are_meaningful(scaffolded_plugin: Path):
    """Regression net — scaffolded tests have assertions, not just `pass`."""
    test_file = scaffolded_plugin / "tests" / "test_plugin.py"
    assert test_file.exists()
    text = test_file.read_text()
    # At least 3 distinct assert statements.
    assert text.count("assert ") >= 3, (
        f"scaffolded test file must contain >=3 assertions, got {text.count('assert ')}"
    )
    # No pass-noop bodies.
    assert "pass  # TODO" not in text
    assert "pass # TODO" not in text
    # At least 2 test functions (lifecycle + protocol minimum).
    test_count = text.count("def test_")
    assert test_count >= 2, f"expected >=2 test functions, got {test_count}"


def test_scaffold_protocol_assertion_present(scaffolded_plugin: Path):
    """Scaffolded tests must assert Plugin Protocol conformance."""
    text = (scaffolded_plugin / "tests" / "test_plugin.py").read_text()
    assert "isinstance" in text and "Plugin" in text, (
        "scaffolded test must verify Plugin Protocol via isinstance check"
    )


def test_scaffold_manifest_v2_assertion_present(scaffolded_plugin: Path):
    """Scaffolded tests must assert the manifest validates against the v2 schema."""
    text = (scaffolded_plugin / "tests" / "test_plugin.py").read_text()
    assert "ManifestV2" in text, "scaffolded test must round-trip ManifestV2"
    assert "manifest_version" in text


def test_scaffold_pyproject_declares_sdk_dep(scaffolded_plugin: Path):
    """Scaffold's pyproject.toml must declare the dryade-plugins-sdk dep."""
    pp = scaffolded_plugin / "pyproject.toml"
    text = pp.read_text()
    assert "dryade-plugins-sdk" in text


def test_scaffold_plugin_module_imports_only_sdk(scaffolded_plugin: Path):
    """Scaffolded plugin.py must not import from core.*."""
    text = (scaffolded_plugin / "plugin.py").read_text()
    # Comment text was already scrubbed; check no actual import statements.
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("from core") or stripped.startswith("import core"):
            pytest.fail(f"violation: scaffolded plugin imports from core: {line!r}")


def test_community_tier_rejected(runner, tmp_path, author_key_dir):
    """--tier community must be rejected with non-zero exit."""
    result = runner.invoke(
        app,
        [
            "plugin",
            "new",
            "bad_plugin",
            "--tier",
            "community",
            "--out",
            str(tmp_path),
        ],
    )
    # The tier callback rejects `community` at parse time (non-zero exit)
    # before any template renders. The rejection-message routing (stdout vs
    # stderr) varies by Click/Typer version, so the stable contract is the
    # non-zero exit plus the fact that nothing was scaffolded.
    assert result.exit_code != 0
    assert not (tmp_path / "bad_plugin").exists(), "community tier must not scaffold"


def test_dev_tier_also_rejected(runner, tmp_path, author_key_dir):
    """Corollary: 'dev' is also not a real plugin tier."""
    result = runner.invoke(
        app,
        ["plugin", "new", "bad", "--tier", "dev", "--out", str(tmp_path)],
    )
    assert result.exit_code != 0


def test_scaffold_mentions_slots(runner, tmp_path, author_key_dir):
    """Disclosure — scaffold output mentions slot consumption."""
    result = runner.invoke(
        app,
        ["plugin", "new", "slot_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    out = result.stdout.lower()
    assert "slot" in out or "custom_plugin_slots" in out, (
        f"scaffold output must disclose slot consumption; got: {result.stdout!r}"
    )


def test_scaffold_cross_links_security_disclosure(runner, tmp_path, author_key_dir):
    """Scaffold output cross-links to security-for-authors."""
    result = runner.invoke(
        app,
        ["plugin", "new", "sec_link", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "security-for-authors" in result.stdout


def test_scaffold_each_valid_tier(runner, tmp_path, author_key_dir):
    """Each valid tier scaffold succeeds and the manifest reflects the tier."""
    for tier in ("starter", "team", "enterprise"):
        sub = tmp_path / tier
        sub.mkdir()
        result = runner.invoke(
            app,
            ["plugin", "new", f"tier_{tier}", "--tier", tier, "--out", str(sub)],
        )
        assert result.exit_code == 0, f"{tier} scaffold failed: {result.stdout}"
        manifest_path = sub / f"tier_{tier}" / "dryade.json"
        assert manifest_path.exists()
        m = json.loads(manifest_path.read_text())
        assert m["required_tier"] == tier
        # Every tier emits v2 manifests.
        assert m["manifest_version"] == "2.0"


def test_scaffold_no_internal_repo_references(runner, tmp_path, author_key_dir):
    """Scaffold output must contain no internal-repo references.

    Tokens are assembled from fragments so the literal forbidden strings never
    appear in this file's own source (which the leak guard also scans).
    """
    forbidden = [
        "dryade-" + "internal",
        "/home/" + "dryade",
        "192.168" + ".",
        "core" + "/ee",
        "plugins" + "_ee",
        "dryade-pm" + " push",
        "core.api" + ".main",
        "gun" + "icorn",
    ]

    result = runner.invoke(
        app,
        ["plugin", "new", "leak_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    plugin_dir = tmp_path / "leak_test"
    for f in plugin_dir.rglob("*"):
        if f.is_file():
            text = f.read_text(errors="ignore")
            for tok in forbidden:
                assert tok not in text, (
                    f"forbidden token {tok!r} leaked into scaffold file {f}"
                )


# ---------------------------------------------------------------------------
# Three-surface tier/slot disclosure regression net.
# ---------------------------------------------------------------------------


def test_scaffold_prints_all_three_tier_ranges(runner, tmp_path, author_key_dir):
    """Scaffold output spells out the tier model and per-tier slot ceilings."""
    result = runner.invoke(
        app,
        ["plugin", "new", "range_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    out = result.stdout.lower()
    # All three tier names are named in the install-reach disclosure.
    for tier in ("starter", "team", "enterprise"):
        assert tier in out, f"Scaffold must mention the {tier} tier. Output: {result.stdout}"
    # The end-user per-tier slot ceilings are spelled out so authors see the
    # slot economy without clicking through.
    assert "5 / 15 / 25" in result.stdout, (
        f"Scaffold must disclose the per-tier slot ceilings. Output: {result.stdout}"
    )


def test_scaffold_links_to_both_docs_pages(runner, tmp_path, author_key_dir):
    """Scaffold cross-links to the tier reference AND the security-for-authors page."""
    result = runner.invoke(
        app,
        ["plugin", "new", "link_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "docs/sdk/concepts" in result.stdout, "Must link to the tier reference"
    assert "/plugins/security-for-authors" in result.stdout, "Must link to the security page"


def test_scaffold_explicitly_states_community_invalid(runner, tmp_path, author_key_dir):
    """Three-surface coverage — scaffold output explicitly disclaims community tier."""
    result = runner.invoke(
        app,
        ["plugin", "new", "invalid_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    out = result.stdout.lower()
    assert "community" in out and ("not" in out or "invalid" in out), (
        f"Scaffold must disclaim community tier. Output: {result.stdout}"
    )


def test_plugin_help_carries_disclosure(runner):
    """Disclosure surface 1: `dryade plugin --help` mentions slot model."""
    result = runner.invoke(app, ["plugin", "--help"])
    assert result.exit_code == 0
    assert "slot" in result.stdout.lower() or "custom_plugin_slots" in result.stdout.lower(), (
        f"`dryade plugin --help` must surface slot model. Output: {result.stdout}"
    )


def test_new_help_does_not_mention_community(runner):
    """`dryade plugin new --help` must not list community as a valid tier."""
    result = runner.invoke(app, ["plugin", "new", "--help"])
    assert result.exit_code == 0
    # Help may mention community in the "NOT a valid" disclaimer — verify negative form.
    lines_with_community = [
        line for line in result.stdout.splitlines() if "community" in line.lower()
    ]
    for line in lines_with_community:
        assert "not" in line.lower() or "invalid" in line.lower(), (
            f"`dryade plugin new --help` mentions community without disclaiming: {line!r}"
        )
