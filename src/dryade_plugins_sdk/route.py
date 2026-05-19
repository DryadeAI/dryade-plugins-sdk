"""Route Protocol — HTTP routes a plugin contributes."""

from __future__ import annotations

from typing import Any, Callable, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class RouteSpec(BaseModel):
    path: str
    method: HttpMethod
    auth_required: bool = True


@runtime_checkable
class Route(Protocol):
    spec: RouteSpec

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def route(
    *, path: str, method: HttpMethod = "GET", auth_required: bool = True
) -> Callable[..., Any]:
    """Decorator that marks a function as a plugin HTTP route handler.

    Usage:
        @route(path="/status", method="GET")
        def status_handler():
            return {"ok": True}
    """

    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        fn.spec = RouteSpec(  # type: ignore[attr-defined]
            path=path, method=method, auth_required=auth_required
        )
        return fn

    return _wrap
