"""Dryade plugin example — tool that calls the host LLM.

Demonstrates two patterns:

1. **Late LLM binding via the host.** The plugin stores a reference to the
   host-provided LLM at ``startup()`` time. The host injects an object that
   structurally satisfies ``llm.complete(prompt) -> str`` (the contract
   ``MockLLM`` exposes from ``dryade_plugins_sdk.testing``).

2. **Leash declaration.** The plugin advertises an isolation policy. The
   host honors it at sandbox-setup time. Plugins that need outbound network
   to reach a remote LLM endpoint should set ``network=True``.

The tool body is deliberately tiny so the example stays readable. Real
plugins compose multiple LLM calls, retry on failure, and emit
structured outputs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from dryade_plugins_sdk import (
    HealthCheck,
    IsolationLevel,
    ManageableComponent,
    tool,
)


@dataclass
class SummarizeLeash:
    """Declarative sandbox policy for this plugin.

    Satisfies the ``Leash`` Protocol structurally. The plugin asks the host
    for outbound network (because real LLM endpoints are remote) and a
    modest memory budget — the host can refuse if its policy disagrees.
    """

    isolation: IsolationLevel = IsolationLevel.PROCESS
    cpu_quota: float | None = 0.5
    memory_mb: int | None = 256
    network: bool = True


# Module-level cache for the host-provided LLM, set by ``startup``.
_llm: Any = None


@tool(
    name="summarize",
    description="Summarize a piece of text using the host LLM.",
)
def summarize(text: str) -> str:
    """Call the host LLM with a summarization prompt."""
    if _llm is None:
        raise RuntimeError(
            "summarize() called before startup wired the host LLM. "
            "This indicates a host lifecycle bug — register → startup must "
            "complete before the tool bus dispatches calls."
        )
    prompt = f"Summarize the following text in one sentence:\n\n{text}"
    return _llm.complete(prompt)


class WithLLMPlugin:
    """Plugin that summarizes text via the host LLM."""

    name = "with_llm"
    version = "0.1.0"
    description = "Dryade plugin example — tool that calls the host LLM via the Leash protocol."
    core_version_constraint = ">=1.0.0,<2.0.0"
    leash = SummarizeLeash()

    def register(self, registry: Any) -> None:
        registry.register(summarize)

    def startup(self, **kwargs: Any) -> None:
        """The host hands us a structurally-typed LLM via kwargs.

        FakeHost passes ``llm=self.llm`` automatically when ``host.load`` is
        called with an extended signature. Production hosts inject the LLM
        the same way.
        """
        global _llm
        _llm = kwargs.get("llm")

    def shutdown(self) -> None:
        global _llm
        _llm = None

    def get_health_checks(self) -> Mapping[str, HealthCheck]:
        return {}

    def get_manageable_components(self) -> Iterable[ManageableComponent]:
        return []


plugin = WithLLMPlugin()
