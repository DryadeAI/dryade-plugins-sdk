<p align="center">
  <a href="https://dryade.ai">
    <img src=".github/images/dryade-logo.svg" alt="Dryade" height="96">
  </a>
</p>

<h1 align="center">dryade-plugins-sdk</h1>

<p align="center">
  <strong>Pure-Protocol Python SDK for authoring Dryade plugins.</strong><br>
  Zero <code>core.*</code> imports. Hash-conformant. DSUL-licensed.
</p>
<h1 align="center">dryade-plugins-sdk</h1>

<p align="center">
  <strong>Build sovereign AI agents that run anywhere.</strong><br>
  Author Dryade plugins in Python with type-safe protocols. Scaffold, validate, package, and ship in one CLI.
</p>

<p align="center">
  <a href="https://github.com/DryadeAI/dryade-plugins-sdk/actions/workflows/ci.yml"><img src="https://github.com/DryadeAI/dryade-plugins-sdk/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/dryade-plugins-sdk/"><img src="https://img.shields.io/pypi/v/dryade-plugins-sdk.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/dryade-plugins-sdk/"><img src="https://img.shields.io/pypi/pyversions/dryade-plugins-sdk.svg" alt="Python versions"></a>
  <a href="https://api.securityscorecards.dev/projects/github.com/DryadeAI/dryade-plugins-sdk"><img src="https://api.securityscorecards.dev/projects/github.com/DryadeAI/dryade-plugins-sdk/badge" alt="OpenSSF Scorecard"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-DSUL-blue.svg" alt="License: DSUL"></a>
  <a href="https://dryade.ai/discord"><img src="https://img.shields.io/badge/Discord-%23plugin--authors-5865F2?logo=discord&logoColor=white" alt="Discord"></a>
  <a href="#contributors"><img src="https://img.shields.io/badge/all_contributors-1-orange.svg" alt="All Contributors"></a>
</p>

<p align="center">
  <img src=".demo/demo.gif" alt="dryade plugin new my-plugin then validate then package in 60 seconds" width="800">
</p>

## Why dryade-plugins-sdk

- **Sovereign** — author plugins that ship to self-hosted Dryade installs. No cloud lock-in.
- **Type-safe** — Python `Protocol` + `@runtime_checkable`. Your IDE catches contract violations before runtime does.
- **Hermetic** — develop and test plugins without installing Dryade. The SDK ships its own test fixtures.

## Quickstart

```bash
uv tool install dryade-cli
dryade plugin new my_plugin --tier starter
cd my_plugin
dryade plugin validate
dryade plugin package
```

Five commands. Your `.dryadepkg` is ready to submit to the [Dryade marketplace](https://dryade.ai/marketplace) or share directly.

Full guide: **[sdk.dryade.ai/getting-started](https://sdk.dryade.ai/getting-started/)**

## Used by

The Dryade team's [first-party plugins](https://dryade.ai/marketplace) are authored with this SDK. Browse the [examples](examples/) directory for 5 reference plugins covering tools, LLM calls, UI bundles, and multi-agent patterns.

## Examples

- [`hello_world/`](examples/hello_world/) — minimal `Plugin` skeleton
- [`with_tool/`](examples/with_tool/) — register a tool the host LLM can call
- [`with_llm/`](examples/with_llm/) — tool that calls the host LLM via the Leash protocol
- [`with_ui/`](examples/with_ui/) — ships a React UI bundle the workbench mounts
- [`multi_agent/`](examples/multi_agent/) — two agents collaborate via shared KV

Start a new plugin from the template starter repo:

```bash
gh repo create my-plugin --template DryadeAI/dryade-plugin-template
```

## Documentation

- **[sdk.dryade.ai](https://sdk.dryade.ai/)** — full docs site (Getting Started, Concepts, API Reference, CLI Reference, Cookbook, FAQ, Migration)
- **[Security model for authors](docs/security.md)** — what you MUST know about hashing, signing, and tier slots
- **[Contract version](docs/concepts.md#contract-version)** — current SDK `CONTRACT_VERSION` and how it gates compatibility

## Community

- **Discord** — [`#plugin-authors`](https://dryade.ai/discord) — ask questions, share what you built
- **GitHub Discussions** — [Q&A](https://github.com/DryadeAI/dryade-plugins-sdk/discussions/categories/q-a) · [Show & Tell](https://github.com/DryadeAI/dryade-plugins-sdk/discussions/categories/show-and-tell) · [Ideas](https://github.com/DryadeAI/dryade-plugins-sdk/discussions/categories/ideas)
- **Twitter/X** — follow [@DryadeAI](https://twitter.com/DryadeAI) for SDK announcements

## Contributing

We welcome contributions. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues are labeled [`good first issue`](https://github.com/DryadeAI/dryade-plugins-sdk/labels/good%20first%20issue).

## Star History

<a href="https://star-history.com/#DryadeAI/dryade-plugins-sdk&Date">
  <img src="https://api.star-history.com/svg?repos=DryadeAI/dryade-plugins-sdk&type=Date" alt="Star History" width="600">
</a>

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not file public issues for vulnerabilities — use [GitHub Security Advisories](https://github.com/DryadeAI/dryade-plugins-sdk/security/advisories/new) or email security@dryade.ai.

## License

[DSUL](LICENSE) (Dryade Source-Usage License). Source-available with explicit usage terms — see LICENSE for details.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->
