"""Factory helpers for building Plugin / Agent / Tool stubs in tests.

D-07: stdlib-only, no dependency on Dryade core.
"""

from __future__ import annotations

from typing import Any, Callable

from dryade_plugins_sdk.plugin import Plugin


class _StubPlugin:
    """Minimal Plugin Protocol-compatible stub.

    Override ``on_register`` to inject custom registration behavior:

        plugin = build_plugin(on_register=lambda r: r.register(my_tool))
    """

    def __init__(self, **kwargs: Any) -> None:
        self.name: str = kwargs.get("name", "stub")
        self.version: str = kwargs.get("version", "0.1.0")
        self.description: str = kwargs.get("description", "stub plugin")
        self.core_version_constraint: str = kwargs.get("core_version_constraint", ">=1.0.0")
        self._on_register: Callable[[Any], None] = kwargs.get("on_register", lambda r: None)

    def register(self, registry: Any) -> None:
        self._on_register(registry)

    def startup(self, **kwargs: Any) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def get_health_checks(self) -> dict[str, Any]:
        return {}

    def get_manageable_components(self) -> list[Any]:
        return []


def build_plugin(**kwargs: Any) -> Plugin:
    """Build a stub Plugin that satisfies the :class:`Plugin` Protocol structurally."""
    return _StubPlugin(**kwargs)  # type: ignore[return-value]


def build_agent(name: str, capability: str = "test") -> Any:
    """Build a stub Agent object — carries the ``_agent_meta`` marker FakeRegistry expects."""

    class _A:
        _agent_meta = {"name": name, "capability": capability, "framework": "test"}

    return _A()


def build_tool(name: str, description: str = "") -> Any:
    """Build a stub Tool callable carrying a ToolSchema on ``.schema``."""
    from dryade_plugins_sdk.tool import ToolSchema

    def _fn(*args: Any, **kwargs: Any) -> None:
        return None

    _fn.schema = ToolSchema(name=name, description=description)  # type: ignore[attr-defined]
    return _fn
