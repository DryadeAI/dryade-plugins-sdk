"""D-12 — doctor diagnostic tests.

Locks down:
- Doctor surfaces stale ``plugin_hash_sha256`` (Rule §9 freshness).
- Doctor surfaces v1 manifests (post-Phase 339-02 they are broken).
- Doctor surfaces Rule §11 violations (``required_tier='community'``).
- Doctor surfaces missing ``dryade.json`` / ``pyproject.toml``.

The tests are the regression net behind T-339-04b-05 (doctor reports OK
when hash is actually stale).
"""

from __future__ import annotations

import json
from pathlib import Path

from dryade_plugins_sdk.cli.cli import app


def test_doctor_on_scaffolded(runner, scaffolded_plugin: Path) -> None:
    """Doctor on a freshly-scaffolded plugin reports green.

    Scaffold has no ``plugin_hash_sha256`` field (that is stamped only by
    ``dryade plugin package``), so the freshness gate is skipped — but every
    other check must pass on the scaffold output.
    """
    result = runner.invoke(app, ["plugin", "doctor", str(scaffolded_plugin)])
    assert result.exit_code == 0, (
        f"clean scaffold must doctor green; got exit {result.exit_code}\n{result.stdout}"
    )
    assert "no issues" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_doctor_detects_stale_hash(runner, scaffolded_plugin: Path) -> None:
    """T-339-04b-05 regression net — doctor MUST flag a stale plugin_hash_sha256."""
    manifest_path = scaffolded_plugin / "dryade.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["plugin_hash_sha256"] = "0" * 64  # not the real hash
    manifest_path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["plugin", "doctor", str(scaffolded_plugin)])
    assert result.exit_code != 0, "stale hash MUST surface as non-zero exit"
    out_lower = result.stdout.lower()
    assert "stale" in out_lower or "mismatch" in out_lower, (
        f"stale-hash report must mention 'stale' or 'mismatch'; got: {result.stdout!r}"
    )


def test_doctor_detects_v1_manifest(runner, scaffolded_plugin: Path) -> None:
    """Doctor flags v1 manifest (broken post-Phase 339-02)."""
    manifest_path = scaffolded_plugin / "dryade.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["manifest_version"] = "1.0"
    manifest_path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["plugin", "doctor", str(scaffolded_plugin)])
    assert result.exit_code != 0, "v1 manifest MUST surface as non-zero exit"
    assert "2.0" in result.stdout, (
        f"v1-manifest report must reference the expected '2.0'; got: {result.stdout!r}"
    )


def test_doctor_detects_community_tier(runner, scaffolded_plugin: Path) -> None:
    """Rule §11 violation — doctor flags required_tier='community' loudly."""
    manifest_path = scaffolded_plugin / "dryade.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["required_tier"] = "community"
    manifest_path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["plugin", "doctor", str(scaffolded_plugin)])
    assert result.exit_code != 0, "community tier MUST surface as non-zero exit"
    out_lower = result.stdout.lower()
    assert "community" in out_lower or "rule §11" in out_lower or "rule 11" in out_lower, (
        f"community-tier report must mention 'community' or 'Rule §11'; got: {result.stdout!r}"
    )


def test_doctor_detects_missing_pyproject(runner, scaffolded_plugin: Path) -> None:
    """Doctor flags missing pyproject.toml (lint_plugins.py would fail on it)."""
    (scaffolded_plugin / "pyproject.toml").unlink()
    result = runner.invoke(app, ["plugin", "doctor", str(scaffolded_plugin)])
    assert result.exit_code != 0, "missing pyproject.toml MUST surface"
    assert "pyproject" in result.stdout.lower(), (
        f"missing-pyproject report must mention pyproject; got: {result.stdout!r}"
    )
