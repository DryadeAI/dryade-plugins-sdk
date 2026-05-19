"""Dryade plugin Protocol.

Authors satisfy this protocol structurally — no inheritance required. Core uses
``isinstance(obj, Plugin)`` to verify at load time, which works because Plugin
is decorated with @runtime_checkable.

This module has ZERO core.* imports (D-05).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable


@dataclass
class HealthCheck:
    """Plugin-declared health check.

    Lifted from core's PluginHealthCheck dataclass shape — pure data, no behavior change.
    Attributes match core/ee/plugins_ee.py:84-103 so plugins built against the SDK
    drop straight into the existing core health monitoring system.
    """

    name: str
    category: str  # "critical" | "important" | "optional"
    check_fn: Callable[[], Any]
    description: str = ""
    timeout_seconds: float = 5.0


@dataclass
class ManageableComponent:
    """Plugin-declared manageable runtime component.

    Lifted from core's ManageableComponent dataclass shape (core/ee/plugins_ee.py:106-127).
    """

    name: str
    type: str
    description: str = ""
    actions: list[str] = field(default_factory=list)
    get_status_fn: Callable[[], Any] | None = None
    execute_action_fn: Callable[[str], Any] | None = None


@runtime_checkable
class Registry(Protocol):
    """Minimal registry contract — what the host injects into Plugin.register."""

    def register(self, item: Any) -> None: ...


@runtime_checkable
class Plugin(Protocol):
    """Dryade plugin contract.

    Required attributes:
        name (str): unique plugin slug
        version (str): semver version
        description (str): human-readable
        core_version_constraint (str): PEP 440 spec, e.g. ">=1.0.0,<2.0.0"

    Required method:
        register(registry): wire agents / tools / routes / hooks

    Optional methods (with default no-op behavior):
        startup, shutdown, get_health_checks, get_manageable_components

    Authors satisfy this protocol structurally. The runtime_checkable decorator
    enables ``isinstance(plugin, Plugin)`` checks in core's loader gate at
    Dryade/core/core/ee/plugins_ee.py:434.

    Security boundary note (T-339-03a-01): @runtime_checkable only validates
    attribute presence, NOT types or method signatures. The Protocol is a
    structural contract — the signed allowlist + plugin hash verification
    remain the authoritative security boundary (Rule §1, §7, §9).
    """

    name: str
    version: str
    description: str
    core_version_constraint: str

    def register(self, registry: Registry) -> None: ...
    def startup(self, **kwargs: Any) -> None: ...
    def shutdown(self) -> None: ...
    def get_health_checks(self) -> Mapping[str, HealthCheck]: ...
    def get_manageable_components(self) -> Iterable[ManageableComponent]: ...
