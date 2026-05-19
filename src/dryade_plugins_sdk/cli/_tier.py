"""Rule §11 tier-enum enforcement.

Lives in its own module so command modules can import ``validate_tier``
without depending on ``dryade_plugins_sdk.cli.cli`` (which imports them, creating a
circular dependency).
"""

from __future__ import annotations

import typer

# Plugin tier names — locked to starter / team / enterprise. ``community`` is
# NOT a valid plugin tier; community users have no PM and no plugins.
VALID_TIERS: set[str] = {"starter", "team", "enterprise"}


def validate_tier(value: str) -> str:
    """Typer callback that enforces Rule §11.

    Plugin tier names are locked to ``starter`` / ``team`` / ``enterprise``.
    ``community`` is NOT a valid plugin tier — community users have no PM and
    no plugins. Rejecting at the CLI surface keeps the invariant out of the
    SDK and the loader.
    """
    if value not in VALID_TIERS:
        raise typer.BadParameter(
            f"tier must be one of {sorted(VALID_TIERS)}, got {value!r}. "
            f"'community' is NOT a valid plugin tier — community users have no Plugin Manager "
            f"and no plugin loading capability. See https://docs.dryade.ai/plugins/tiers"
        )
    return value
