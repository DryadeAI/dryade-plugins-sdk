"""F4.2 BREAKER: scaffold output must pass lint_plugins.py against v2 schema.
F4.3 BREAKER: scaffolded tests must be meaningful (not pass-no-op).
F4.4: scaffold path must be discoverable from `dryade plugin new --help`.
Rule §11: `--tier community` must be rejected.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
    """F4.2: manifest_version must be exactly '2.0' and no entry_point (D-02)."""
    manifest = json.loads((scaffolded_plugin / "dryade.json").read_text())
    assert manifest["manifest_version"] == "2.0"
    assert "entry_point" not in manifest, "D-02: v2 manifests must not carry entry_point"
    assert manifest["required_tier"] == "starter"
    assert manifest["name"] == "test_plugin"


def test_scaffold_passes_lint(scaffolded_plugin: Path):
    """F4.2 regression net — dryade-plugins/tools/lint_plugins.py must pass.

    Calls the lint with an absolute path so the lint's REPO_ROOT-relative
    arg-resolution falls through to the absolute-path branch (REPO_ROOT/arg
    returns arg when arg is absolute).
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    lint = repo_root / "dryade-plugins" / "tools" / "lint_plugins.py"
    if not lint.exists():
        pytest.skip(f"lint_plugins.py not found at {lint}")
    # Stage scaffold under a fake tier dir so the lint's tier-cross-check passes.
    staging = scaffolded_plugin.parent / "lint_root" / "starter"
    staging.mkdir(parents=True)
    plugin_in_tier = staging / scaffolded_plugin.name
    shutil.copytree(scaffolded_plugin, plugin_in_tier)
    result = subprocess.run(
        [sys.executable, str(lint), str(plugin_in_tier)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"lint failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_scaffold_tests_are_meaningful(scaffolded_plugin: Path):
    """F4.3 regression net — scaffolded tests have assertions, not just `pass`."""
    test_file = scaffolded_plugin / "tests" / "test_plugin.py"
    assert test_file.exists()
    text = test_file.read_text()
    # At least 3 distinct assert statements per F4.3 must-have.
    assert text.count("assert ") >= 3, (
        f"F4.3: scaffolded test file must contain >=3 assertions, got {text.count('assert ')}"
    )
    # No pass-noop bodies.
    assert "pass  # TODO" not in text
    assert "pass # TODO" not in text
    # At least 2 test functions (lifecycle + protocol minimum).
    test_count = text.count("def test_")
    assert test_count >= 2, f"F4.3: expected >=2 test functions, got {test_count}"


def test_scaffold_protocol_assertion_present(scaffolded_plugin: Path):
    """F4.3: tests must assert Plugin Protocol conformance."""
    text = (scaffolded_plugin / "tests" / "test_plugin.py").read_text()
    assert "isinstance" in text and "Plugin" in text, (
        "F4.3: scaffolded test must verify Plugin Protocol via isinstance check"
    )


def test_scaffold_manifest_v2_assertion_present(scaffolded_plugin: Path):
    """F4.3: tests must assert manifest validates against v2 schema."""
    text = (scaffolded_plugin / "tests" / "test_plugin.py").read_text()
    assert "ManifestV2" in text, "F4.3: scaffolded test must round-trip ManifestV2"
    assert "manifest_version" in text


def test_scaffold_pyproject_declares_sdk_dep(scaffolded_plugin: Path):
    """Scaffold's pyproject.toml must declare the dryade-plugins-sdk dep."""
    pp = scaffolded_plugin / "pyproject.toml"
    text = pp.read_text()
    assert "dryade-plugins-sdk" in text


def test_scaffold_plugin_module_imports_only_sdk(scaffolded_plugin: Path):
    """D-05: scaffolded plugin.py must not import from core.*."""
    text = (scaffolded_plugin / "plugin.py").read_text()
    # Comment text was already scrubbed; check no actual import statements.
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("from core") or stripped.startswith("import core"):
            pytest.fail(f"D-05 violation: scaffolded plugin imports from core: {line!r}")


def test_community_tier_rejected(runner, tmp_path, author_key_dir):
    """Rule §11: --tier community must be rejected with non-zero exit."""
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
    assert result.exit_code != 0
    # Typer's BadParameter writes to stdout in CliRunner output.
    combined = (result.stdout or "") + (str(result.exception) or "")
    assert "community" in combined.lower() or "starter" in combined.lower()


def test_dev_tier_also_rejected(runner, tmp_path, author_key_dir):
    """Rule §11 corollary: 'dev' is also not a real plugin tier."""
    result = runner.invoke(
        app,
        ["plugin", "new", "bad", "--tier", "dev", "--out", str(tmp_path)],
    )
    assert result.exit_code != 0


def test_scaffold_mentions_slots(runner, tmp_path, author_key_dir):
    """D-10 disclosure — scaffold output mentions slot consumption."""
    result = runner.invoke(
        app,
        ["plugin", "new", "slot_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    out = result.stdout.lower()
    assert "slot" in out or "custom_plugin_slots" in out, (
        f"D-10: scaffold output must disclose slot consumption; got: {result.stdout!r}"
    )


def test_scaffold_cross_links_security_disclosure(runner, tmp_path, author_key_dir):
    """F6.5 partial closure — scaffold output cross-links to security-for-authors."""
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
    """T-339-04a-03: scaffold output must contain no internal-repo references."""
    result = runner.invoke(
        app,
        ["plugin", "new", "leak_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    plugin_dir = tmp_path / "leak_test"
    for f in plugin_dir.rglob("*"):
        if f.is_file():
            text = f.read_text(errors="ignore")
            for forbidden in ("dryade-internal", "192.168.", "gh_token", "/home/dryade"):
                assert forbidden not in text, f"T-339-04a-03: forbidden token {forbidden!r} in {f}"


# ---------------------------------------------------------------------------
# 339-07 additions — three-surface tier/slot disclosure regression net.
# ---------------------------------------------------------------------------


def test_scaffold_prints_all_three_tier_ranges(runner, tmp_path, author_key_dir):
    """D-10 + F7.4 — scaffold output spells out slot ranges for all three tiers."""
    result = runner.invoke(
        app,
        ["plugin", "new", "range_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    out = result.stdout.lower()
    assert "starter" in out and ("1-3" in out or "1 to 3" in out), (
        f"Scaffold must mention starter slot range. Output: {result.stdout}"
    )
    assert "team" in out and ("3-5" in out or "3 to 5" in out), (
        f"Scaffold must mention team slot range. Output: {result.stdout}"
    )
    assert "enterprise" in out and "10" in out, (
        f"Scaffold must mention enterprise slot range. Output: {result.stdout}"
    )


def test_scaffold_links_to_both_docs_pages(runner, tmp_path, author_key_dir):
    """3-surface coverage — scaffold cross-links to tiers.md AND security-for-authors.md."""
    result = runner.invoke(
        app,
        ["plugin", "new", "link_test", "--tier", "starter", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "/plugins/tiers" in result.stdout, "Must link to tiers.md"
    assert "/plugins/security-for-authors" in result.stdout, "Must link to security-for-authors.md"


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
