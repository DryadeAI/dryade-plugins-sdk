"""Database session Protocol — minimal contract.

Plugins should NOT define their own SQLAlchemy Base — they get host.db.Base.
F3.9 finding tracked: per-plugin Base classes break Alembic; the SDK declares
the session contract here, the host injects a single shared Base when needed.

This module has ZERO core.* imports (D-05).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DBSession(Protocol):
    """Minimal DB session contract — host injects a real SQLAlchemy Session."""

    def execute(self, statement: Any) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
