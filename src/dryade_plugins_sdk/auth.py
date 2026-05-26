"""Auth dependency Protocols.

These do NOT import from core.auth. They declare the callable shapes the host
will inject. Plugin authors type-hint against these Protocols; the host's
real implementations live in core (out of SDK).

This module has zero host-runtime imports — it is a pure contract.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class CurrentUser(Protocol):
    """Shape of the user object injected by the host.

    Plugins should treat this as read-only. The host populates ``is_admin`` from
    the user's role at the time of request.
    """

    id: str
    email: str
    is_admin: bool


# Callable shapes the host injects into FastAPI route signatures.
# Plugins import these and use them as type annotations on Depends() callbacks.
GetCurrentUser = Callable[[Any], CurrentUser]  # host injects, returns CurrentUser
RequireAdmin = Callable[[Any], CurrentUser]  # 403 if not admin
GetDb = Callable[[Any], Any]  # host injects DB session


__all__ = ["CurrentUser", "GetCurrentUser", "RequireAdmin", "GetDb"]
