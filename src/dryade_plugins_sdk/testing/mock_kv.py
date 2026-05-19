"""In-memory MockKV — drop-in for the KV Protocol in tests.

D-07: stdlib-only, no dependency on Dryade core.
"""

from __future__ import annotations

from time import time as _now
from typing import Any


class MockKV:
    """In-memory key-value store with optional TTL semantics.

    Satisfies the :class:`dryade_plugins_sdk.kv.KV` Protocol structurally.
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        if key not in self._data:
            return default
        value, expiry = self._data[key]
        if expiry is not None and _now() > expiry:
            del self._data[key]
            return default
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expiry = _now() + ttl_seconds if ttl_seconds else None
        self._data[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def has(self, key: str) -> bool:
        _MISSING = object()
        return self.get(key, _MISSING) is not _MISSING

    def keys(self, prefix: str = "") -> list[str]:
        # Sweep expired entries lazily, then return matching keys.
        for k in list(self._data.keys()):
            self.get(k)  # triggers eviction if expired
        return [k for k in self._data.keys() if k.startswith(prefix)]
