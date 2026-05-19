"""Decorator re-export module — single import for authors."""

from __future__ import annotations

from typing import Any, Callable

from dryade_plugins_sdk.route import route
from dryade_plugins_sdk.tool import tool


def agent(*, name: str, capability: str, framework: str = "crewai") -> Callable[..., Any]:
    """Decorator that marks a class as a plugin agent.

    Usage:
        @agent(name="my_agent", capability="summarize")
        class MyAgent:
            ...
    """

    def _wrap(cls: Any) -> Any:
        cls._agent_meta = {
            "name": name,
            "capability": capability,
            "framework": framework,
        }
        return cls

    return _wrap


__all__ = ["tool", "route", "agent"]
