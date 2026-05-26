"""Plugin tier-enum enforcement.

Lives in its own module so command modules can import ``validate_tier``
without depending on ``dryade_plugins_sdk.cli.cli`` (which imports them, creating a
circular dependency).
"""

from __future__ import annotations

import typer

# Plugin tier names — locked to starter / team / enterprise. ``community`` is
# not a valid plugin tier.
VALID_TIERS: set[str] = {"starter", "team", "enterprise"}


def validate_tier(value: str) -> str:
    """Typer callback that enforces the valid plugin-tier set.

    Plugin tier names are locked to ``starter`` / ``team`` / ``enterprise``.
    ``community`` is not a valid plugin tier. Rejecting at the CLI surface
    keeps the invariant out of the SDK and the loader.
    """
    if value not in VALID_TIERS:
        raise typer.BadParameter(
            f"tier must be one of {sorted(VALID_TIERS)}, got {value!r}. "
            f"'community' is not a valid plugin tier. "
            f"See https://docs.dryade.ai/plugins/tiers"
        )
    return value
