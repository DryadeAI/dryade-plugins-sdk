"""ConfigStore Protocol — plugin reads/writes persistent settings via host."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Config(Protocol):
    """The host provides a Config impl; plugins call .get() / .patch().

    The ``plugin_name`` first-arg is OPTIONAL — if omitted, host uses the
    calling plugin's name (existing plugins rely on this signature).
    """

    def get(self, plugin_name: str | None = None) -> dict[str, Any]: ...

    def patch(
        self,
        plugin_name: str | dict[str, Any] | None = None,
        updates: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...
