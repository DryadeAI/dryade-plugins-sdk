"""FakeHost — in-memory host implementing Plugin's Registry contract.

Authors can pytest plugins without spinning up the host runtime.

This module has ZERO core.* imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dryade_plugins_sdk.plugin import Plugin


@dataclass
class FakeRegistry:
    """Records what a plugin registers — agents, tools, routes, hooks, health checks.

    The dispatch logic discriminates by attribute shape rather than by class
    identity so any object structurally satisfying the SDK Protocols sorts into
    the right bucket. Catch-all: ``components``.
    """

    routes: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, Any] = field(default_factory=dict)
    tools: dict[str, Any] = field(default_factory=dict)
    health_checks: dict[str, Any] = field(default_factory=dict)
    components: list[Any] = field(default_factory=list)

    def register(self, item: Any) -> None:
        """Discriminate by attribute to fan out to the right bucket."""
        if hasattr(item, "spec") and hasattr(item.spec, "path"):
            # RouteSpec exposes .path
            self.routes[item.spec.path] = item
        elif hasattr(item, "schema") and hasattr(item.schema, "name"):
            # ToolSchema exposes .name
            self.tools[item.schema.name] = item
        elif hasattr(item, "_agent_meta"):
            # @agent decorator stamps _agent_meta dict
            self.agents[item._agent_meta["name"]] = item
        elif hasattr(item, "category") and hasattr(item, "check_fn"):
            # HealthCheck dataclass
            self.health_checks[item.name] = item
        else:
            self.components.append(item)


class FakeHost:
    """Composed host stub.

    Provides:
      - ``registry`` (FakeRegistry) — record of what the plugin registered.
      - ``kv`` (MockKV) — in-memory KV.
      - ``config`` (MockConfig) — in-memory config provider.
      - ``llm`` (MockLLM) — scripted LLM stub.

    Lifecycle:
      ``load(plugin)`` calls ``plugin.register(registry)`` then
      ``plugin.startup()``. ``shutdown()`` calls ``plugin.shutdown()`` in
      reverse load order.
    """

    def __init__(self) -> None:
        self.registry = FakeRegistry()
        # Lazy imports to keep import time short and avoid a cycle if a future
        # mock_* module ever wants to import FakeHost.
        from dryade_plugins_sdk.testing.mock_kv import MockKV
        from dryade_plugins_sdk.testing.mock_config import MockConfig
        from dryade_plugins_sdk.testing.mock_llm import MockLLM

        self.kv = MockKV()
        self.config = MockConfig()
        self.llm = MockLLM()
        self.loaded: list[Plugin] = []

    def load(self, plugin: Plugin) -> None:
        """Simulate the plugin load lifecycle: register → startup."""
        plugin.register(self.registry)
        plugin.startup()
        self.loaded.append(plugin)

    def shutdown(self) -> None:
        """Call shutdown on every loaded plugin in reverse order."""
        for plugin in reversed(self.loaded):
            plugin.shutdown()
        self.loaded.clear()
