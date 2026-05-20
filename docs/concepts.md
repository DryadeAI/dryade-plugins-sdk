# Concepts

The mental model behind the SDK in 800 words.

## Protocols, not base classes

The SDK defines `Plugin`, `Agent`, `Tool`, `Route`, `Config`, `KV`, `Leash`
as **`typing.Protocol` subclasses** with the `@runtime_checkable` decorator.
You implement these contracts **structurally** — by having the right
attributes and methods — instead of inheriting from an ABC.

```python
from dryade_plugins_sdk import Plugin

class MyPlugin:                                    # NO base class
    name = "my_plugin"
    version = "0.1.0"
    description = "..."
    core_version_constraint = ">=1.0.0,<2.0.0"
    def register(self, registry): ...

assert isinstance(MyPlugin(), Plugin)              # True — structural match
```

This means:

- **Your IDE catches missing methods at edit time** — without you needing
  to import the SDK at every layer.
- **The host can verify conformance at load time** with a single
  `isinstance(plugin, Plugin)` call.
- **You never inherit Dryade's implementation details** — protocols are a
  one-way contract.

## Manifest v2

Every plugin ships a `dryade.json` at its root. v2 (the only supported
version) has a strict JSON schema with these required fields:

| Field | Type | Notes |
|-------|------|-------|
| `manifest_version` | `"2.0"` | locked |
| `name` | string, snake_case | matches the directory name |
| `version` | semver | strict 2.0.0 |
| `description` | string | shown in marketplace cards |
| `required_tier` | `starter` / `team` / `enterprise` | **Rule §11 — never `community`** |
| `author` | string | your name or org |
| `core_version_constraint` | PEP 440 spec | e.g. `>=1.0.0,<2.0.0` |

Optional fields cover UI bundles, sandbox policy, MCP servers, agent
metadata, and more — see [API Reference](api-reference.md#manifestv2) for
the full surface.

## Tiers

- **`starter`** — single-author plugins, max 1 user, no custom plugin slots.
- **`team`** — up to N users from the same org (`max_users` in the signed
  allowlist).
- **`enterprise`** — full multi-org slot allocation.

Tier limits are **enforced by the Dryade host** based on the signed
allowlist, not by the SDK or CLI. The CLI rejects `--tier community` at
scaffold + validate + package time (Rule §11) because the platform itself
has no community tier.

## Signing

Authors generate an Ed25519 keypair via `dryade plugin keygen`. The CLI
embeds the public key in the `.dryadepkg` and signs the manifest's hash
with the private key. Private keys live at `~/.dryade-author/dev-key.priv`
with mode `0o600` — the CLI refuses to load weaker permissions.

When you submit to the marketplace, the marketplace **re-signs** with its
own dual Ed25519 + ML-DSA-65 keys before publishing in the signed allowlist.
Authors never see the production signing material.

## SBOM — embedded CycloneDX

Every `.dryadepkg` produced by `dryade plugin package` carries an
embedded CycloneDX 1.5 SBOM at `sbom.cdx.json`. The packager tries
`cyclonedx-py` first (full SBOM with components and dependencies). If
`cyclonedx-py` is not on `PATH` the SBOM falls back to a minimal shim
with the component metadata only — the shim is flagged via
`metadata.properties[dryade:sbom-source = "minimal-shim"]` so consumers
can distinguish the two at audit time. The manifest also carries an
`sbom` field with the same source string so downstream provenance
checks can read it without opening the SBOM file.

## Routes — `@route` decorator

Plugins can expose HTTP endpoints by decorating methods with `@route`:

```python
from dryade_plugins_sdk import build_router, route

class MyPlugin:
    name = "my_plugin"
    # ...

    @route(path="/status", method="GET")
    def status(self):
        return {"ok": True}

    def register(self, registry):
        registry.register(build_router(self))
```

`build_router(plugin)` walks the plugin via `collect_routes(plugin)`,
binds every decorated method onto a fresh FastAPI `APIRouter`, and
returns it. Plugins that already construct their own `self.router`
get that router back unchanged — no double-mount. FastAPI is imported
lazily, so plugins without routes don't pull FastAPI into the SDK's
import path.

## Hashing — contract version 4

Every plugin source file gets hashed with **both SHA-256 and SHA3-256**.
The pair is computed by walking the plugin tree, collecting every `.py`
file, and chaining `path:content` segments through both hash families. The
final 64-char hex digests land in `plugin_hash_sha256` and
`plugin_hash_sha3_256` fields of the packaged manifest.

The host re-computes both digests at load time and refuses to load if
either drifts. The `compute_plugin_hash_pair` function in
`dryade_plugins_sdk.packaging` is the canonical implementation;
`tests/test_hash_conformance.py` independently reimplements it in stdlib
to catch drift.

The current contract version is **4**. SDK consumers should pin
`dryade-plugins-sdk>=1.0.0,<2.0.0` to stay on contract 4 — a future major
SDK bump signals a hash-algorithm change.

## Sandbox / Leash

Plugins can advertise an isolation policy via a `Leash` attribute on the
plugin class or instance:

```python
from dryade_plugins_sdk import IsolationLevel

class MyLeash:
    isolation: IsolationLevel = IsolationLevel.PROCESS
    cpu_quota: float | None = 0.5
    memory_mb: int | None = 512
    network: bool = True

class MyPlugin:
    leash = MyLeash()
    ...
```

The host honors the Leash if it can (live levels: `NONE`, `PROCESS`,
`LANGUAGE`). Levels declared as future support (`CONTAINER`, `GVISOR`)
fail-closed at the host until the sandbox lands — see
[`examples/with_llm/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples/with_llm)
for the canonical request shape.

## Contract version

The constant `dryade_plugins_sdk.CONTRACT_VERSION` (also accessible as
`__contract_version__`) is **4** at this SDK release. Plugins built against
SDK 1.x will continue to load on hosts that advertise contract 4. A future
SDK 2.0 will signal a contract bump (e.g. switch hash family, add a
required field) and host loaders will refuse plugins from the older
contract.

You usually do not need to read this value at runtime — the `dryade-cli`
embeds it in the packaged manifest's `contract_version` field, and the
host validates at load.
