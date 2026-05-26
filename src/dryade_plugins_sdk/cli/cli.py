"""dryade CLI — typer-based author tooling.

Binary name: ``dryade`` (bound via pyproject.toml [project.scripts]).
Top-level: ``dryade plugin <subcommand>``.

This is the author CLI. End-users run ``dryade-pm`` (a different binary, in Rust).
"""

from __future__ import annotations

import typer

# Re-export VALID_TIERS / validate_tier for backwards compatibility with any
# callers that imported from dryade_plugins_sdk.cli.cli before the helper moved
# into dryade_plugins_sdk.cli._tier (split out to escape a circular import once
# command modules began consuming the callback). 'community' is not a valid
# plugin tier and the callback at dryade_plugins_sdk.cli._tier.validate_tier rejects it
# at parse time before any template renders.
from dryade_plugins_sdk.cli.commands.new import new_plugin
from dryade_plugins_sdk.cli.commands.package import package_plugin
from dryade_plugins_sdk.cli.commands.validate import validate_plugin

# keygen + doctor are soft-imported so the core CLI works without them:
try:
    from dryade_plugins_sdk.cli.commands.doctor import doctor
    from dryade_plugins_sdk.cli.commands.keygen import keygen

    _KEYGEN_DOCTOR_AVAILABLE = True
except ImportError:
    _KEYGEN_DOCTOR_AVAILABLE = False


app = typer.Typer(
    name="dryade",
    help="Dryade plugin author CLI",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

plugin_app = typer.Typer(
    name="plugin",
    help=(
        "Plugin lifecycle commands.\n\n"
        "Every plugin you ship consumes one of the end-user's custom_plugin_slots.\n"
        "Pick --tier carefully: starter (1-3 slots typical), team (3-5), enterprise (10+).\n"
        "Slot ranges: https://docs.dryade.ai/plugins/tiers\n"
        "Author obligations: https://docs.dryade.ai/plugins/security-for-authors"
    ),
    no_args_is_help=True,
)
app.add_typer(plugin_app, name="plugin")

# Register each subcommand.
plugin_app.command("new", help="Scaffold a new Dryade plugin")(new_plugin)
plugin_app.command(
    "validate",
    help="Validate a plugin against the SDK contract",
)(validate_plugin)
plugin_app.command(
    "package",
    help="Produce a signed .dryadepkg for marketplace submission",
)(package_plugin)

if _KEYGEN_DOCTOR_AVAILABLE:
    plugin_app.command("keygen", help="Generate or rotate your author signing key")(keygen)
    plugin_app.command("doctor", help="Diagnose plugin issues")(doctor)


def main() -> None:
    """Entrypoint bound by pyproject.toml [project.scripts]."""
    app()


if __name__ == "__main__":
    main()
