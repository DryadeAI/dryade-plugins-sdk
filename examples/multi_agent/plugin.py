"""Dryade plugin example — two agents collaborate via shared KV.

Pattern: ``researcher`` gathers raw findings and writes them under a KV key.
``summarizer`` reads that key, compresses the content, and writes the
summary back under a sibling key. The host orchestrates the call order
based on each agent's capability metadata.

The shared KV is the host-provided ``KV`` Protocol implementation. In tests
we use ``MockKV`` from ``dryade_plugins_sdk.testing``. In production the
host injects a real KV bound to the plugin's namespace.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from dryade_plugins_sdk import (
    AgentCard,
    AgentCapability,
    AgentFramework,
    AgentResult,
    HealthCheck,
    ManageableComponent,
)


class _AgentBase:
    """Common scaffolding for the two collaborating agents.

    Stamps ``_agent_meta`` so the FakeRegistry routes the instance into
    ``registry.agents`` at register time.
    """

    name: str
    capability: str
    description: str

    def __init__(self, kv: Any) -> None:
        self._kv = kv
        self._agent_meta = {"name": self.name}

    def get_card(self) -> AgentCard:
        return AgentCard(
            name=self.name,
            description=self.description,
            version="0.1.0",
            framework=AgentFramework.CREWAI,
            capabilities=[AgentCapability(name=self.capability, description=self.description)],
        )

    def get_tools(self) -> list[dict[str, Any]]:
        return []


class ResearcherAgent(_AgentBase):
    """First leg: gathers raw findings and writes them to shared KV."""

    name = "researcher"
    capability = "gather"
    description = "Collects raw findings under the shared KV key."

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        findings = [f"Finding A about: {task}", f"Finding B about: {task}"]
        self._kv.set("multi_agent:findings", findings)
        return AgentResult(result=findings, status="ok")


class SummarizerAgent(_AgentBase):
    """Second leg: reads findings and writes a summary back."""

    name = "summarizer"
    capability = "compress"
    description = "Compresses the researcher's findings into a one-line summary."

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        findings = self._kv.get("multi_agent:findings", [])
        if not findings:
            return AgentResult(
                result=None,
                status="error",
                error="No findings to summarize — researcher must run first.",
            )
        summary = f"{len(findings)} findings on '{task}'."
        self._kv.set("multi_agent:summary", summary)
        return AgentResult(result=summary, status="ok")


class MultiAgentPlugin:
    """Plugin orchestrating two agents that share state through KV."""

    name = "multi_agent"
    version = "0.1.0"
    description = "Dryade plugin example — two agents collaborate via shared KV."
    core_version_constraint = ">=1.0.0,<2.0.0"

    def __init__(self) -> None:
        self.researcher: ResearcherAgent | None = None
        self.summarizer: SummarizerAgent | None = None

    def register(self, registry: Any) -> None:
        """register() needs a KV to construct the agents. The host injects KV
        via ``host.kv``; in tests we materialize via FakeHost's MockKV."""
        # The agents need a KV reference but register() doesn't take kwargs.
        # We bind to a lazy-resolved KV that startup() will swap in.
        kv = getattr(self, "_kv", None)
        self.researcher = ResearcherAgent(kv)
        self.summarizer = SummarizerAgent(kv)
        registry.register(self.researcher)
        registry.register(self.summarizer)

    def startup(self, **kwargs: Any) -> None:
        """The host injects a KV bound to this plugin's namespace."""
        kv = kwargs.get("kv")
        if kv is not None:
            self._kv = kv
            if self.researcher is not None:
                self.researcher._kv = kv
            if self.summarizer is not None:
                self.summarizer._kv = kv

    def shutdown(self) -> None:
        pass

    def get_health_checks(self) -> Mapping[str, HealthCheck]:
        return {}

    def get_manageable_components(self) -> Iterable[ManageableComponent]:
        return []


plugin = MultiAgentPlugin()
