"""KV Protocol — opaque key-value store contract for plugins.

The host provides an implementation backed by SQLite, Redis, or in-memory.
Plugins should treat this as eventually consistent and key-scoped by plugin name.

This module has zero host-runtime imports — it is a pure contract.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KV(Protocol):
    """Plugin-facing KV store contract.

    Host injects a real implementation (SQLite/Redis/in-memory). Plugins should
    treat it as eventually consistent and key-scoped by their plugin name.
    """

    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...
    def delete(self, key: str) -> bool: ...
    def has(self, key: str) -> bool: ...
    def keys(self, prefix: str = "") -> list[str]: ...
