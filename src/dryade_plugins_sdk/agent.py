"""Agent Protocol and supporting Pydantic models.

Mirrors the host's universal agent contract (the UniversalAgent ABC + models),
inverted to a @runtime_checkable Protocol with zero host-runtime imports.

This module has zero host-runtime imports — it is a pure contract. The
AgentExecutionError exception is defined in dryade_plugins_sdk.exceptions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel


class AgentFramework(str, Enum):
    """Supported agent frameworks."""

    CREWAI = "crewai"
    LANGCHAIN = "langchain"
    ADK = "adk"
    A2A = "a2a"
    MCP = "mcp"
    CUSTOM = "custom"


class OutputContract(BaseModel):
    """Declarative description of an agent capability's output shape.

    Sourced from the optional `agent_metadata` block in dryade.json.
    Missing block -> adapter leaves output_contract unset -> planner falls back
    to today's keyword-match behavior. Backward-compatible by construction.
    """

    output_format: Literal[
        "text",
        "structured_json",
        "email",
        "markdown",
        "html",
        "code",
        "binary",
    ]
    output_schema: dict[str, Any] | None = None
    deterministic: bool = False
    suitable_for: list[str] = []
    not_suitable_for: list[str] = []
    requires_post_processing: bool = False


class AgentCapability(BaseModel):
    """Describes what an agent can do."""

    name: str
    description: str
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    output_contract: OutputContract | None = None


class AgentCapabilities(BaseModel):
    """Runtime capabilities of an agent for orchestrator negotiation.

    Used by DryadeOrchestrator to validate agent supports required features
    before calling (capability negotiation pattern).
    """

    supports_streaming: bool = False
    supports_memory: bool = False
    supports_knowledge: bool = False
    supports_delegation: bool = False
    supports_callbacks: bool = False
    supports_resources: bool = False  # MCP resources
    supports_prompts: bool = False  # MCP prompts
    supports_sessions: bool = False  # ADK sessions
    supports_artifacts: bool = False  # ADK artifacts
    supports_async_tasks: bool = False  # A2A long-running
    supports_push: bool = False  # A2A push notifications
    max_retries: int = 3
    timeout_seconds: int = 60
    is_critical: bool = False
    framework_specific: dict[str, Any] = {}


class AgentCard(BaseModel):
    """Agent discovery card (inspired by A2A protocol).

    See: https://github.com/a2aproject/A2A
    """

    name: str
    description: str
    version: str
    capabilities: list[AgentCapability] = []
    framework: AgentFramework
    endpoint: str | None = None  # For A2A remote agents
    metadata: dict[str, Any] = {}
    skills: list[str] = []  # Names of injected skills
    primary_output_format: str | None = None


class AgentResult(BaseModel):
    """Standard result format for all agents."""

    result: Any
    status: str  # "ok", "error", "partial"
    error: str | None = None
    metadata: dict[str, Any] = {}

    @property
    def output(self) -> Any:
        """Alias for result field - for backward compatibility with router code."""
        return self.result


@runtime_checkable
class Agent(Protocol):
    """Universal agent contract.

    Plugin agents satisfy this protocol structurally. Core adapters
    (CrewAI / LangChain / ADK / A2A / MCP / custom) all conform to the
    same surface so the orchestrator can call them uniformly.
    """

    def get_card(self) -> AgentCard: ...
    async def execute(self, task: str, context: dict[str, Any] | None = None) -> AgentResult: ...
    def get_tools(self) -> list[dict[str, Any]]: ...
