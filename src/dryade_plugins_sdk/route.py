"""Route Protocol — HTTP routes a plugin contributes.

The ``@route`` decorator stamps route metadata on the wrapped callable so
the host (or the SDK helpers ``collect_routes`` / ``build_router``) can
discover plugin-contributed routes by attribute shape, without an
explicit registry call from the author.

Decorator-stashed metadata lives at two attribute names for backwards
compatibility:

  - ``_dryade_route_meta`` (canonical, dict) — used by ``collect_routes``
    and ``build_router`` and the contract going forward.
  - ``spec`` (``RouteSpec``) — historical attribute name; kept so existing
    ``Route`` Protocol consumers and downstream code that already reads
    ``fn.spec`` keep working.

The host imports these helpers lazily at plugin-load time. Authors can
also call ``build_router(plugin)`` directly inside their plugin's
``register()`` and hand the result to whatever mount API the host
exposes — useful for plugins that want full control over how their
router is composed.
"""

from __future__ import annotations

from typing import Any, Callable, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class RouteSpec(BaseModel):
    path: str
    method: HttpMethod
    auth_required: bool = True
    name: str | None = None


@runtime_checkable
class Route(Protocol):
    spec: RouteSpec

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def route(
    *,
    path: str,
    method: HttpMethod = "GET",
    auth_required: bool = True,
    name: str | None = None,
) -> Callable[..., Any]:
    """Decorator that marks a function as a plugin HTTP route handler.

    Stamps two attributes on the wrapped callable:

      - ``_dryade_route_meta`` — canonical dict consumed by
        ``dryade_plugins_sdk.plugin.collect_routes`` /
        ``build_router``. Shape: ``{"path", "method", "auth_required",
        "name"}``.
      - ``spec`` — equivalent ``RouteSpec`` (kept for backwards
        compatibility with code that already reads ``fn.spec``).

    Usage::

        from dryade_plugins_sdk import route

        @route(path="/status", method="GET")
        def status_handler():
            return {"ok": True}

    The plugin's ``register()`` can then call
    ``router = build_router(self); registry.register(router)`` or the
    host can call ``collect_routes(plugin)`` itself to discover every
    decorated route on the plugin instance.
    """

    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        meta: dict[str, Any] = {
            "path": path,
            "method": method,
            "auth_required": auth_required,
            "name": name,
        }
        fn._dryade_route_meta = meta  # type: ignore[attr-defined]
        fn.spec = RouteSpec(  # type: ignore[attr-defined]
            path=path, method=method, auth_required=auth_required, name=name
        )
        return fn

    return _wrap
