"""The smallest plugin that satisfies the Plugin Protocol.

Demonstrates the absolute minimum: name, version, description,
core_version_constraint, and a `register` method that does nothing.

Lifecycle hooks (startup, shutdown, get_health_checks,
get_manageable_components) get sensible no-op defaults. Authors can override
any of them — the host will call whatever is present.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from dryade_plugins_sdk import HealthCheck, ManageableComponent


class HelloWorldPlugin:
    """The simplest possible Dryade plugin."""

    name = "hello_world"
    version = "0.1.0"
    description = "Minimal Dryade plugin — the smallest thing that satisfies the Plugin Protocol."
    core_version_constraint = ">=1.0.0,<2.0.0"

    def register(self, registry: Any) -> None:
        """No agents / tools / routes — this example is the bare contract."""

    def startup(self, **kwargs: Any) -> None:
        """Called once after all plugins load."""

    def shutdown(self) -> None:
        """Called on graceful shutdown."""

    def get_health_checks(self) -> Mapping[str, HealthCheck]:
        return {}

    def get_manageable_components(self) -> Iterable[ManageableComponent]:
        return []


plugin = HelloWorldPlugin()
