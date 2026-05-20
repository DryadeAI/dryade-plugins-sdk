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


def collect_routes(plugin: Any) -> list[tuple[dict[str, Any], Callable[..., Any]]]:
    """Walk a plugin instance and return every method decorated with ``@route``.

    Returns a list of ``(meta, callable)`` tuples ordered by ``__qualname__``
    so ordering is stable across runs (helpful for tests and for OpenAPI
    generation where deterministic output matters).

    A method counts as a route if it has the canonical
    ``_dryade_route_meta`` attribute (stamped by the ``@route`` decorator).
    Methods that only carry the legacy ``spec`` attribute are also picked
    up so older plugins keep working.
    """
    collected: list[tuple[dict[str, Any], Callable[..., Any]]] = []
    seen: set[int] = set()
    for attr_name in dir(plugin):
        if attr_name.startswith("__"):
            continue
        try:
            attr = getattr(plugin, attr_name)
        except Exception:
            continue
        if not callable(attr):
            continue
        if id(attr) in seen:
            continue
        meta: dict[str, Any] | None = getattr(attr, "_dryade_route_meta", None)
        if meta is None:
            spec = getattr(attr, "spec", None)
            if spec is not None and hasattr(spec, "path") and hasattr(spec, "method"):
                meta = {
                    "path": getattr(spec, "path"),
                    "method": getattr(spec, "method"),
                    "auth_required": getattr(spec, "auth_required", True),
                    "name": getattr(spec, "name", None),
                }
        if meta is None:
            continue
        seen.add(id(attr))
        collected.append((meta, attr))

    collected.sort(key=lambda pair: getattr(pair[1], "__qualname__", pair[0].get("path", "")))
    return collected


def build_router(plugin: Any) -> Any:
    """Build a FastAPI ``APIRouter`` from a plugin's decorated handlers.

    Behavior:

      - If the plugin already exposes ``self.router`` (the legacy pattern
        used by plugins that construct their own ``APIRouter`` and mount
        it via ``register()``), return that router unchanged. This avoids
        double-mount and keeps the legacy pattern working unchanged.
      - Otherwise walk the plugin via :func:`collect_routes` and bind
        every ``(meta, callable)`` onto a fresh ``APIRouter`` with the
        appropriate HTTP method.

    FastAPI is imported lazily so the SDK itself does not pull FastAPI
    into authors' development environments unless they actually need
    routes.

    Raises:
        ImportError: if the plugin has at least one decorated route and
            FastAPI is not installed.
    """
    legacy_router = getattr(plugin, "router", None)
    if legacy_router is not None:
        return legacy_router

    routes = collect_routes(plugin)
    if not routes:
        # No decorated routes — return an empty APIRouter so the host
        # can still treat the plugin uniformly. Lazy-import so callers
        # without FastAPI keep working when the plugin has no routes.
        try:
            from fastapi import APIRouter
        except ImportError:  # pragma: no cover - fast path
            return None
        return APIRouter()

    from fastapi import APIRouter

    router = APIRouter()
    for meta, handler in routes:
        method = str(meta.get("method", "GET")).upper()
        kwargs: dict[str, Any] = {}
        if meta.get("name"):
            kwargs["name"] = meta["name"]
        router.add_api_route(
            meta["path"],
            handler,
            methods=[method],
            **kwargs,
        )
    return router


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
