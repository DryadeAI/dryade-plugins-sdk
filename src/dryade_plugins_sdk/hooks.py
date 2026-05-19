"""Observability hook decorators — no-op shims in SDK, wrapped by host at runtime.

Plugin authors annotate their functions with @traced and @hook; the host's
observability layer detects the marker attributes and wraps the call with an
OpenTelemetry span or a lifecycle subscription.

This module has ZERO core.* imports (D-05).
"""

from __future__ import annotations

from typing import Any, Callable


def traced(name: str | None = None) -> Callable[..., Any]:
    """Mark a function for tracing.

    At plugin load time the host wraps the function with an OpenTelemetry span.
    In the SDK this is a no-op decorator that records the desired span name on
    the function object via the ``_traced_name`` attribute.

    Example:
        @traced("my_plugin.do_work")
        def do_work(...): ...
    """

    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        fn._traced_name = name or fn.__name__  # type: ignore[attr-defined]
        return fn

    return _wrap


def hook(event: str) -> Callable[..., Any]:
    """Mark a function as a lifecycle hook for an event.

    The host scans the plugin's exported callables for ``_hook_event`` and
    subscribes them to the matching pub/sub topic at load time.

    Example:
        @hook("plugin.startup")
        def on_startup(...): ...
    """

    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        fn._hook_event = event  # type: ignore[attr-defined]
        return fn

    return _wrap


__all__ = ["traced", "hook"]
