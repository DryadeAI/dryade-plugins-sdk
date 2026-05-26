"""validate command — fails closed, no --skip-validation, no community tier."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dryade_plugins_sdk.cli.cli import app


def test_validate_passes_on_scaffolded(runner, scaffolded_plugin: Path):
    """A fresh scaffold must pass validate end-to-end."""
    # Clear sys.modules cache so each test gets a clean import.
    sys.modules.pop("test_plugin", None)
    result = runner.invoke(app, ["plugin", "validate", str(scaffolded_plugin)])
    assert result.exit_code == 0, f"validate failed unexpectedly: {result.stdout}"


def test_fails_closed_on_v1_manifest(runner, scaffolded_plugin: Path):
    """Fail-closed: v1 manifest must exit non-zero."""
    sys.modules.pop("test_plugin", None)
    bad = scaffolded_plugin / "dryade.json"
    bad.write_text(
        json.dumps(
            {
                "manifest_version": "1.0",
                "name": "test_plugin",
                "version": "0.1.0",
                "description": "bad",
                "required_tier": "starter",
                "author": "x",
                "core_version_constraint": ">=1.0.0,<2.0.0",
            }
        )
    )
    result = runner.invoke(app, ["plugin", "validate", str(scaffolded_plugin)])
    assert result.exit_code != 0


def test_fails_closed_on_missing_required_field(runner, scaffolded_plugin: Path):
    """Fail-closed: manifest missing a required field must exit non-zero."""
    sys.modules.pop("test_plugin", None)
    bad = scaffolded_plugin / "dryade.json"
    bad.write_text(json.dumps({"manifest_version": "2.0", "name": "no_other_fields"}))
    result = runner.invoke(app, ["plugin", "validate", str(scaffolded_plugin)])
    assert result.exit_code != 0


def test_fails_closed_on_missing_dryade_json(runner, scaffolded_plugin: Path):
    """Fail-closed: no manifest at all must exit non-zero."""
    sys.modules.pop("test_plugin", None)
    (scaffolded_plugin / "dryade.json").unlink()
    result = runner.invoke(app, ["plugin", "validate", str(scaffolded_plugin)])
    assert result.exit_code != 0


def test_no_skip_validation_flag(runner):
    """Fail-closed: --skip-validation / --bypass / --unsafe must NOT exist."""
    result = runner.invoke(app, ["plugin", "validate", "--help"])
    text = result.stdout
    assert "--skip-validation" not in text
    assert "--bypass" not in text
    assert "--unsafe" not in text
    assert "--force" not in text


def test_community_tier_in_manifest_rejected(runner, scaffolded_plugin: Path):
    """SDK side: manifest with required_tier=community must be rejected."""
    sys.modules.pop("test_plugin", None)
    manifest_path = scaffolded_plugin / "dryade.json"
    data = json.loads(manifest_path.read_text())
    data["required_tier"] = "community"
    manifest_path.write_text(json.dumps(data))
    result = runner.invoke(app, ["plugin", "validate", str(scaffolded_plugin)])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Defense-in-depth: CLI-level tier gate in validate.
# ---------------------------------------------------------------------------


def test_validate_rejects_community_manifest_with_helpful_message(runner, scaffolded_plugin: Path):
    """Defense-in-depth — validate rejects a manifest with required_tier='community'
    and prints a valid-tiers reference + docs URL."""
    sys.modules.pop("test_plugin", None)
    manifest_path = scaffolded_plugin / "dryade.json"
    m = json.loads(manifest_path.read_text())
    m["required_tier"] = "community"
    manifest_path.write_text(json.dumps(m))
    result = runner.invoke(app, ["plugin", "validate", str(scaffolded_plugin)])
    assert result.exit_code != 0
    out = result.stdout.lower()
    assert "community" in out
    assert "/plugins/tiers" in result.stdout or "valid tiers" in out


def test_validate_does_not_have_skip_tier_check_flag(runner):
    """Fail-closed — no `--skip-tier-check` or `--allow-community-tier` flag exists."""
    result = runner.invoke(app, ["plugin", "validate", "--help"])
    assert "--skip-tier-check" not in result.stdout
    assert "--allow-community-tier" not in result.stdout
    assert "--unsafe-tier" not in result.stdout
