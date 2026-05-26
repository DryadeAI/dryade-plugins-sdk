# dryade-plugins-sdk

**Build sovereign AI agents that run anywhere.**

Author Dryade plugins in Python with type-safe protocols. Scaffold, validate,
package, and ship in one CLI.

## Why this SDK

- **Sovereign** — author plugins that ship to self-hosted Dryade installs.
  No cloud lock-in.
- **Type-safe** — Python `Protocol` + `@runtime_checkable`. Your IDE catches
  contract violations before runtime does.
- **Hermetic** — develop and test plugins without installing Dryade. The SDK
  ships its own test fixtures.

## 30-second quickstart

```bash
uv tool install dryade-cli
dryade plugin new my_plugin --tier starter
cd my_plugin
dryade plugin validate
dryade plugin package
```

Five commands. Your `.dryadepkg` is ready to submit to the
[Dryade marketplace](https://dryade.ai/marketplace) or share directly.

Walk through the full tutorial in **[Getting Started](getting-started.md)**.

## Map of the docs

| Page | What it covers |
|------|----------------|
| [Getting Started](getting-started.md) | 5-step tutorial — install through package |
| [Concepts](concepts.md) | Protocols, manifest v2, tiers, signing, contract version |
| [API Reference](api-reference.md) | Every public symbol in the SDK |
| [CLI Reference](cli-reference.md) | Every dryade-cli command + flag |
| [Examples](examples.md) | Five reference plugins linked from `examples/` |
| [Cookbook](cookbook.md) | Recipes — HITL, MCP tool, multi-agent, KV, UI |
| [Security](security.md) | What plugin authors must know about hashing + slots |
| [Migration](migration.md) | Notes for internal contributors moving off manifest v1 |
| [FAQ](faq.md) | Common questions; 10 entries; covers the early-author friction |
| [Changelog](changelog.md) | Versioned release notes |

## Community

- **Discord** — [GitHub Discussions](https://github.com/DryadeAI/dryade-plugins-sdk/discussions)
- **GitHub Discussions** — Q&A, Show & Tell, Ideas
- **Twitter/X** — [@DryadeAI](https://twitter.com/DryadeAI)
