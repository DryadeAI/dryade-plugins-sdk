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

from dryade_plugins_sdk.plugin import (
    Plugin,
    HealthCheck,
    ManageableComponent,
    collect_routes,
    build_router,
)
from dryade_plugins_sdk.agent import (
    Agent,
    AgentFramework,
    AgentCapability,
    AgentCapabilities,
    AgentResult,
    AgentCard,
    OutputContract,
)
from dryade_plugins_sdk.tool import Tool, tool
from dryade_plugins_sdk.route import Route, route
from dryade_plugins_sdk.config import Config
from dryade_plugins_sdk.kv import KV
from dryade_plugins_sdk.leash import Leash, IsolationLevel
from dryade_plugins_sdk.hooks import traced, hook
from dryade_plugins_sdk.exceptions import (
    DryadePluginError,
    PluginValidationError,
    ManifestValidationError,
    AgentExecutionError,
    HashMismatchError,
)
from dryade_plugins_sdk.manifest import ManifestV2
from dryade_plugins_sdk.packaging import (
    CONTRACT_VERSION,
    compute_plugin_hash_pair,
    sign_manifest,
    load_private_key,
    verify_plugin_hash,
)

__version__ = "1.1.5"
__contract_version__ = 4  # SHA-256 + SHA3-256 dual hash

__all__ = [
    # Core protocols
    "Plugin",
    "HealthCheck",
    "ManageableComponent",
    "Agent",
    "AgentFramework",
    "AgentCapability",
    "AgentCapabilities",
    "AgentResult",
    "AgentCard",
    "OutputContract",
    "Tool",
    "tool",
    "Route",
    "route",
    "collect_routes",
    "build_router",
    "Config",
    # Supporting protocols
    "KV",
    "Leash",
    "IsolationLevel",
    # Hook decorators
    "traced",
    "hook",
    # Exceptions
    "DryadePluginError",
    "PluginValidationError",
    "ManifestValidationError",
    "AgentExecutionError",
    "HashMismatchError",
    # Manifest
    "ManifestV2",
    # Packaging primitives
    "CONTRACT_VERSION",
    "compute_plugin_hash_pair",
    "sign_manifest",
    "load_private_key",
    "verify_plugin_hash",
    # Version info
    "__version__",
    "__contract_version__",
]
