# API Reference

The full public surface of `dryade_plugins_sdk`. Importable from the
top-level package — internal sub-modules are an implementation detail and
may change between minor versions.

## Core protocols

### `Plugin`

The contract every plugin must satisfy. Decorated with
`@runtime_checkable` so `isinstance(obj, Plugin)` works at load time.

**Required attributes:**

- `name: str` — unique plugin slug, snake_case.
- `version: str` — semver 2.0.0.
- `description: str` — human-readable.
- `core_version_constraint: str` — PEP 440 spec.

**Required method:**

- `register(registry: Registry) -> None`

**Optional methods (with default no-op behavior):**

- `startup(**kwargs) -> None`
- `shutdown() -> None`
- `get_health_checks() -> Mapping[str, HealthCheck]`
- `get_manageable_components() -> Iterable[ManageableComponent]`

### `Agent`

Universal agent contract — plugin agents satisfy this and the host's
adapter calls them uniformly across CrewAI / LangChain / ADK / A2A / MCP.

**Methods:**

- `get_card() -> AgentCard`
- `async execute(task: str, context: dict | None = None) -> AgentResult`
- `get_tools() -> list[dict]`

### `Tool`

A plugin tool — callable with a `ToolSchema` attribute.

Use the `@tool(name=..., description=...)` decorator to stamp the schema
onto a plain function.

### `Route`

A plugin HTTP route handler — callable with a `RouteSpec` attribute.

Use the `@route(path=..., method=...)` decorator to register an HTTP path.

### `Config`

Per-plugin runtime configuration — the host injects a Config implementation.

### `KV`

Per-plugin key-value store with optional TTL. The host injects an
implementation that namespaces keys to your plugin.

### `Leash` + `IsolationLevel`

Sandbox-policy declaration (see [Concepts § Leash](concepts.md#sandbox--leash)).

## Supporting models

- `HealthCheck` — dataclass for plugin-declared health checks.
- `ManageableComponent` — dataclass for runtime-manageable components.
- `AgentFramework` — enum (`CREWAI`, `LANGCHAIN`, `ADK`, `A2A`, `MCP`, `CUSTOM`).
- `AgentCard`, `AgentCapability`, `AgentCapabilities`, `AgentResult`,
  `OutputContract` — Pydantic models for agent metadata.

## Manifest

### `ManifestV2`

Dataclass wrapper over the v2 JSON schema. Construct it with the manifest
dict and it raises `ManifestValidationError` if anything fails the schema.

```python
import json
from dryade_plugins_sdk import ManifestV2

data = json.loads(open("dryade.json").read())
known = ManifestV2.__dataclass_fields__
manifest = ManifestV2(**{k: v for k, v in data.items() if k in known})
```

## Packaging

### `CONTRACT_VERSION`

Integer constant — current value `4`.

### `compute_plugin_hash_pair(plugin_dir: Path) -> tuple[str, str]`

Walks the plugin directory, hashes every `.py` file under SHA-256 +
SHA3-256, returns the `(sha256_hex, sha3_256_hex)` pair.

### `sign_manifest(manifest: dict, private_key_path: Path) -> dict`

Adds `signature` (128-char hex Ed25519) and optional `signature_pq`
fields. Mutates and returns the manifest.

### `load_private_key(path: Path)`

Loads an Ed25519 private key, asserting mode `0o600` (fails closed
otherwise).

### `verify_plugin_hash(manifest: dict, plugin_dir: Path) -> bool`

Re-computes both hashes and asserts equality with the manifest fields.
Used by `dryade plugin validate` and (re-implemented) by Dryade core's
loader.

## Hooks

- `@traced(name=...)` — stamps `_traced_name` on the function. The host
  wraps it with an OpenTelemetry span at load time.
- `@hook(event=...)` — stamps `_hook_event`. The host subscribes the
  function to the matching pub/sub topic.

## Exceptions

- `DryadePluginError` — base.
- `PluginValidationError` — `--tier community`, schema fail, missing
  attribute.
- `ManifestValidationError` — manifest schema mismatch.
- `AgentExecutionError` — agent runtime failure.
- `HashMismatchError` — plugin source hash drift.

## Testing fixtures (`dryade_plugins_sdk.testing`)

Fixtures so authors `pytest` without installing the host runtime:

- `FakeHost` — in-memory host. Use `host.load(plugin)` then assert against
  `host.registry.tools`, `host.registry.routes`, `host.registry.agents`,
  `host.registry.health_checks`, `host.registry.components`.
- `FakeRegistry` — what `FakeHost.registry` returns.
- `MockKV` — TTL-aware in-memory KV.
- `MockConfig` — patchable in-memory Config.
- `MockLLM(responses=[...])` — scripted LLM stub. Records every call as
  `LLMCall`.
- `build_plugin`, `build_agent`, `build_tool` — factory helpers.

## Version info

- `__version__` — SDK version string.
- `__contract_version__` — current plugin contract (4).
