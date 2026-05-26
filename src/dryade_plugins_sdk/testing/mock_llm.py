"""Deterministic MockLLM — records calls, returns scripted responses.

Stdlib-only, with no dependency on the host runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMCall:
    """One recorded call to the MockLLM — useful for assertions in tests."""

    prompt: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)


class MockLLM:
    """A scripted LLM stub.

    Pass a list of strings on construction; calls return them in order, cycling
    when exhausted. Useful for testing agent retry / fallback logic.
    """

    def __init__(self, responses: list[str] | None = None) -> None:
        self.calls: list[LLMCall] = []
        self.responses: list[str] = list(responses or ["mocked response"])
        self._cursor = 0

    def complete(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append(LLMCall(prompt=prompt, kwargs=kwargs))
        resp = self.responses[self._cursor % len(self.responses)]
        self._cursor += 1
        return resp

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        self.calls.append(LLMCall(prompt="", messages=messages, kwargs=kwargs))
        resp = self.responses[self._cursor % len(self.responses)]
        self._cursor += 1
        return resp

    def reset(self) -> None:
        self.calls.clear()
        self._cursor = 0
