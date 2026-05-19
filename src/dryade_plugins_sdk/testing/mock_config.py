"""In-memory MockConfig — Config Protocol drop-in for tests.

D-07: stdlib-only, no dependency on Dryade core.
"""

from __future__ import annotations

from typing import Any


class MockConfig:
    """In-memory plugin config provider.

    Methods mirror the host's Config Protocol: ``get(plugin_name)`` returns a
    dict, ``patch(...)`` shallow-merges updates. The shortcut form
    ``patch({"key": "value"})`` patches the implicit ``__caller__`` namespace
    so tests don't need to thread the plugin name through every call.
    """

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def get(self, plugin_name: str | None = None) -> dict[str, Any]:
        return self._data.get(plugin_name or "__caller__", {}).copy()

    def patch(
        self,
        plugin_name: str | dict[str, Any] | None = None,
        updates: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Single-arg shortcut: patch({"key": "value"}) targets __caller__.
        if isinstance(plugin_name, dict):
            updates = plugin_name
            plugin_name = "__caller__"
        elif plugin_name is None:
            plugin_name = "__caller__"
        cur = self._data.setdefault(plugin_name, {})
        cur.update(updates or {})
        return cur.copy()
