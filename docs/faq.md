# FAQ

The questions we have seen first-time authors ask. Open a
[Discussion](https://github.com/DryadeAI/dryade-plugins-sdk/discussions/categories/q-a)
if yours is not here.

## 1. Do I need to install the Dryade runtime to author a plugin?

**No.** The SDK is a pure-contract package. Install `dryade-plugins-sdk`
from PyPI, run `pytest`, and your plugin is ready to package. The
`dryade_plugins_sdk.testing` subpackage ships in-memory mocks (FakeHost,
MockKV, MockConfig, MockLLM) so you can unit-test without spinning up
the platform.

## 2. Why structural Protocols instead of base classes?

Three reasons:

1. **No inheritance coupling** — you can satisfy `Plugin` from an
   existing class without rewriting it.
2. **IDE accuracy** — `typing.Protocol` lets mypy / pylance type-check
   conformance at edit time.
3. **Host has zero leverage on your imports** — you can build a plugin
   that only imports from `dryade_plugins_sdk` and stdlib.

## 3. What's `required_tier` for?

It tells the host's allowlist what privilege class your plugin needs.
Valid values: `starter`, `team`, `enterprise`. The host enforces tier
limits (max_users, custom_plugin_slots) from the signed allowlist;
the SDK refuses `community` (Rule §11) at every level.

## 4. Can I bypass the hash check for development?

**No.** The CLI is fail-closed (Rule §4). The host accepts plugins whose
on-disk hash matches the manifest-embedded hash, full stop. For local
iteration, re-run `dryade plugin package` after every code change — it
takes <1s and produces a fresh hash.

## 5. How do I share state between plugin invocations?

Two options:

1. **`KV`** — TTL-aware key-value store, host-namespaced to your plugin.
   See [Cookbook §4](cookbook.md#4-persistent-kv--ttl-aware-caching).
2. **`DB`** — the host injects a SQLAlchemy session bound to a per-plugin
   schema. Use this for relational data your plugin owns.

Module-level globals work, but they reset on plugin reload. Avoid for
anything you would not be happy to lose.

## 6. Where do plugin tools run?

Inside the plugin's Leash sandbox. Live levels are `NONE`, `PROCESS`, and
`LANGUAGE` (bwrap/firejail user namespace). `CONTAINER` and `GVISOR` are
declared but **fail-closed** at the host until the corresponding sandbox
lands. Authors should pick the strictest level their tool can survive in.

## 7. What's the difference between the SDK and the host?

- **SDK (`dryade-plugins-sdk`)** — pure-contract package on PyPI. Defines
  Protocols + manifest schema + packaging primitives. Zero `core.*` imports.
- **Host (Dryade platform)** — the runtime that loads plugins, enforces
  the signed allowlist, mounts UI bundles, routes tool calls. Source at
  `github.com/DryadeAI/Dryade`.

Authors only interact with the SDK. The host implements the SDK's
Protocols, not the other way around.

## 8. Why is `community` rejected as a tier?

The Dryade platform has no community tier — community users have no
Plugin Manager and no plugins at all. Plugins ship to paying customers
(`starter` / `team` / `enterprise`). Rule §11 enforces this at every
scaffold / validate / package step.

## 9. How do I get my plugin into the marketplace?

Submit the `.dryadepkg` produced by `dryade plugin package` to the
marketplace at https://dryade.ai/marketplace. The marketplace verifies
your dev signature, re-signs with its dual Ed25519 + ML-DSA-65 production
keys, and publishes in the signed allowlist that customer installs pull.

## 10. Can I distribute plugins outside the marketplace?

Yes — share the `.dryadepkg` directly. Customers can install with
`dryade-pm install <path>` (the Plugin Manager binary, separate from the
authoring CLI). The signed allowlist still gates the plugin at load time
on the customer's Dryade install, so the customer's PM must explicitly
allow your dev signing key.
