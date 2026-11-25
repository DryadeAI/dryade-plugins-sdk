"""Dryade plugin SDK — Protocol contracts for plugin authors.

PURE CONTRACT: zero imports from the host runtime. Authors satisfy these protocols structurally — the runtime checks shape, not inheritance.

This module re-exports the stable public surface:
  - Core protocols: Plugin / Agent / Tool / Route / Config + supporting models
  - Supporting protocols: KV / Leash / IsolationLevel
  - Packaging primitives: compute_plugin_hash_pair / sign_manifest /
    CONTRACT_VERSION (the dual-hash plugin contract: SHA-256 + SHA3-256)
  - Hook decorators: traced / hook (no-op shims; host wraps at runtime)
  - Exception hierarchy: DryadePluginError + four children
  - ManifestV2 dataclass validating against the bundled v2 JSON schema
"""

from __future__ import annotations

from dryade_plugins_sdk.agent import (
    Agent,
    AgentCapabilities,
    AgentCapability,
    AgentCard,
    AgentFramework,
    AgentResult,
    OutputContract,
)
from dryade_plugins_sdk.config import Config
from dryade_plugins_sdk.exceptions import (
    AgentExecutionError,
    DryadePluginError,
    HashMismatchError,
    ManifestValidationError,
    PluginValidationError,
)
from dryade_plugins_sdk.hooks import hook, traced
from dryade_plugins_sdk.kv import KV
from dryade_plugins_sdk.leash import IsolationLevel, Leash
from dryade_plugins_sdk.manifest import ManifestV2
from dryade_plugins_sdk.packaging import (
    CONTRACT_VERSION,
    compute_plugin_hash_pair,
    load_private_key,
    sign_manifest,
    verify_plugin_hash,
)
from dryade_plugins_sdk.plugin import (
    HealthCheck,
    ManageableComponent,
    Plugin,
    build_router,
    collect_routes,
)
from dryade_plugins_sdk.route import Route, route
from dryade_plugins_sdk.tool import Tool, tool

__version__ = "1.1.5"
__contract_version__ = 4  # SHA-256 + SHA3-256 dual hash

__all__ = [
    # Packaging primitives
    "CONTRACT_VERSION",
    # Supporting protocols
    "KV",
    "Agent",
    "AgentCapabilities",
    "AgentCapability",
    "AgentCard",
    "AgentExecutionError",
    "AgentFramework",
    "AgentResult",
    "Config",
    # Exceptions
    "DryadePluginError",
    "HashMismatchError",
    "HealthCheck",
    "IsolationLevel",
    "Leash",
    "ManageableComponent",
    # Manifest
    "ManifestV2",
    "ManifestValidationError",
    "OutputContract",
    # Core protocols
    "Plugin",
    "PluginValidationError",
    "Route",
    "Tool",
    "__contract_version__",
    # Version info
    "__version__",
    "build_router",
    "collect_routes",
    "compute_plugin_hash_pair",
    "hook",
    "load_private_key",
    "route",
    "sign_manifest",
    "tool",
    # Hook decorators
    "traced",
    "verify_plugin_hash",
]
