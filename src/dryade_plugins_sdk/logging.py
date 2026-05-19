"""Plugin logging helper — thin wrapper over stdlib logging.

This module has ZERO core.* imports (D-05).
"""

from __future__ import annotations

import logging as _stdlib_logging


def get_logger(plugin_name: str) -> _stdlib_logging.Logger:
    """Return a namespaced logger named ``dryade.plugin.<plugin_name>``.

    All plugin log records flow through stdlib logging so the host's existing
    log handlers / formatters / filters apply automatically.
    """

    return _stdlib_logging.getLogger(f"dryade.plugin.{plugin_name}")


__all__ = ["get_logger"]
