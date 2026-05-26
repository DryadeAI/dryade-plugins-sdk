"""dryade plugin validate — fail-closed local validation.

Fails closed: any error exits non-zero. The command exposes
no validation-bypass option of any kind. The validation surface mirrors the loader's gate:
v2 manifest schema, Plugin Protocol structural conformance, importable
package layout.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from dryade_plugins_sdk import Plugin
from dryade_plugins_sdk.exceptions import ManifestValidationError, PluginValidationError
from dryade_plugins_sdk.manifest import ManifestV2


def validate_plugin(
    plugin_dir: Annotated[Path, typer.Argument(help="Plugin directory")] = Path("."),
) -> None:
    """Validate a plugin's manifest, Protocol conformance, and package hygiene."""
    plugin_dir = plugin_dir.resolve()
    errors: list[str] = []

    manifest_path = plugin_dir / "dryade.json"
    if not manifest_path.exists():
        typer.secho(f"Missing {manifest_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        typer.secho(f"Invalid JSON in dryade.json: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Explicit tier gate (defense in depth — ManifestV2 also rejects but the
    # typer-level error message is more actionable than a schema-validation
    # stack trace). 'community' is not a valid required_tier.
    manifest_tier = manifest.get("required_tier")
    if manifest_tier == "community":
        typer.secho(
            "required_tier='community' is not allowed.\n"
            "  'community' is not a valid plugin tier.\n"
            "  Valid tiers: starter, team, enterprise.\n"
            "  See: https://docs.dryade.ai/plugins/tiers",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # Manifest schema (v2; tier validity enforced via the SDK ManifestV2).
    try:
        known = ManifestV2.__dataclass_fields__
        ManifestV2(**{k: v for k, v in manifest.items() if k in known})
    except (ManifestValidationError, PluginValidationError, TypeError) as e:
        errors.append(f"Manifest validation: {e}")

    if not (plugin_dir / "pyproject.toml").exists():
        errors.append("Missing pyproject.toml")

    if not (plugin_dir / "__init__.py").exists():
        errors.append("Missing __init__.py")

    # Protocol conformance — import the plugin module and check
    # isinstance(plugin, Plugin). Cleared from sys.modules first so consecutive
    # CliRunner invocations don't see stale caches.
    sys.path.insert(0, str(plugin_dir.parent))
    sys.modules.pop(plugin_dir.name, None)
    try:
        mod = importlib.import_module(plugin_dir.name)
        if not hasattr(mod, "plugin"):
            errors.append(f"Module {plugin_dir.name} has no `plugin` attribute (see plugin.py)")
        elif not isinstance(mod.plugin, Plugin):
            errors.append(
                f"`{plugin_dir.name}.plugin` does not satisfy "
                f"dryade_plugins_sdk.Plugin Protocol. Required attributes: "
                f"name, version, description, core_version_constraint, register."
            )
    except ImportError as e:
        errors.append(f"Cannot import {plugin_dir.name}: {e}")
    finally:
        if sys.path and sys.path[0] == str(plugin_dir.parent):
            sys.path.pop(0)

    if errors:
        typer.secho(
            f"Validation FAILED ({len(errors)} errors):",
            fg=typer.colors.RED,
            bold=True,
        )
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=1)

    typer.secho("Validation passed", fg=typer.colors.GREEN)
