# Migration

Notes for plugin authors moving between SDK versions or between manifest
schema versions.

## SDK 0.x → 1.0

External authors did not have a 0.x SDK to migrate from — 1.0 is the
first public release. This section is preserved for internal contributors
who built plugins against pre-1.0 prototype contracts.

### Manifest v1 → v2

The schema changed in several places. The most common updates:

| v1 field | v2 equivalent |
|----------|---------------|
| `entry_point` | **removed** — plugins are imported via the package's `__init__.py:plugin` symbol |
| `plugin_settings` | `settings_schema` (JSON Schema) |
| `has_routes: true` | `api_paths` array (list of mounted paths) |
| `env_vars` | `settings_schema` properties with `env` mapping |
| `dependencies: {...}` | `pyproject.toml` `[project.dependencies]` |
| `capabilities` | `agent_metadata.capabilities` (per-agent block) |
| `plugin_type` | `category` |

The CLI's `dryade plugin validate` will surface schema violations with
the offending path so migrations are straightforward.

### Decorator changes

The pre-1.0 `@DryadeAgent` decorator became simple structural conformance
to the `Agent` Protocol. If your class had `@DryadeAgent` and the agent
attributes (`get_card`, `execute`, `get_tools`), drop the decorator and
verify `isinstance(MyAgent(), Agent)` returns `True`.

### Hash algorithm

Contract v3 used SHA-256 only. **Contract v4 dual-hashes with SHA-256 +
SHA3-256.** Re-package any plugin you intend to ship on v4 — the
marketplace verifies both hashes at submit time.

## Future migrations

When SDK 2.0 lands, this page will document:

- Any Protocol method-signature changes.
- The contract version bump (if any).
- Manifest schema delta from v2.0 → v3.0 (if any).
- Re-package + re-sign steps.

We maintain a **3-month overlap window** at every major bump: hosts honor
both the old and new contract for one quarter so authors have time to
re-package without breaking installs.

## Pinning advice

```toml
# pyproject.toml
[project]
dependencies = [
    "dryade-plugins-sdk>=1.0.0,<2.0.0",  # contract v4
]
```

The upper bound prevents accidental contract-bump breakage on a
transitive update. When SDK 2.0 lands, bump the bound *after* you have
re-packaged your plugin.
