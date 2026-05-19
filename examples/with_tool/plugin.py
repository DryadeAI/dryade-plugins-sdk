"""Dryade plugin example — exposes one Tool the host LLM can call.

The ``@tool`` decorator stamps a ``ToolSchema`` on the function. At load time
the host's FakeRegistry (or production registry) discriminates by attribute
shape and routes the callable to the tool bus.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from dryade_plugins_sdk import HealthCheck, ManageableComponent, tool


@tool(
    name="get_current_time",
    description="Return the current UTC time as ISO 8601.",
)
def get_current_time() -> str:
    """Tool body — pure stdlib, deterministic except for the clock."""
    return datetime.now(timezone.utc).isoformat()


class WithToolPlugin:
    """Plugin that exposes one tool."""

    name = "with_tool"
    version = "0.1.0"
    description = "Dryade plugin example — registers one tool the host LLM can call."
    core_version_constraint = ">=1.0.0,<2.0.0"

    def register(self, registry: Any) -> None:
        registry.register(get_current_time)

    def startup(self, **kwargs: Any) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def get_health_checks(self) -> Mapping[str, HealthCheck]:
        return {}

    def get_manageable_components(self) -> Iterable[ManageableComponent]:
        return []


plugin = WithToolPlugin()
