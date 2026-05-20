"""Dryade plugin example — one ``@tool`` for the host LLM + one ``@route``
HTTP endpoint that calls it.

The ``@tool`` decorator stamps a ``ToolSchema`` on the function. The
``@route`` decorator stamps ``_dryade_route_meta`` so
``build_router(plugin)`` can produce a FastAPI ``APIRouter`` from the
plugin's decorated methods. The host (or the plugin's own ``register``)
mounts the router under the plugin's namespace.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from dryade_plugins_sdk import (
    HealthCheck,
    ManageableComponent,
    build_router,
    route,
    tool,
)


@tool(
    name="get_current_time",
    description="Return the current UTC time as ISO 8601.",
)
def get_current_time() -> str:
    """Tool body — pure stdlib, deterministic except for the clock."""
    return datetime.now(timezone.utc).isoformat()


class WithToolPlugin:
    """Plugin that exposes one tool and one route."""

    name = "with_tool"
    version = "0.1.0"
    description = "Dryade plugin example — registers one tool and one HTTP route."
    core_version_constraint = ">=1.0.0,<2.0.0"

    @route(path="/now", method="GET", auth_required=True)
    def now(self) -> dict[str, str]:
        """HTTP endpoint that returns the current UTC time as JSON.

        Mounted under the plugin's namespace by ``build_router(self)``.
        """
        return {"utc": get_current_time()}

    def register(self, registry: Any) -> None:
        # Register the tool with the host's tool bus.
        registry.register(get_current_time)
        # Build a FastAPI router from every @route-decorated method on
        # this plugin and register it with the host. The host knows how
        # to mount an APIRouter under the plugin's prefix.
        registry.register(build_router(self))

    def startup(self, **kwargs: Any) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def get_health_checks(self) -> Mapping[str, HealthCheck]:
        return {}

    def get_manageable_components(self) -> Iterable[ManageableComponent]:
        return []


plugin = WithToolPlugin()
