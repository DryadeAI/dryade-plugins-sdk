<p align="center">
  <a href="https://dryade.ai">
    <img src=".github/images/dryade-logo.svg" alt="Dryade" height="96">
  </a>
</p>

<h1 align="center">dryade-plugins-sdk</h1>

<p align="center">
  <strong>Pure-Protocol Python SDK for authoring Dryade plugins.</strong><br>
  Zero host-runtime imports. Hash-conformant. MIT-licensed.
</p>
  <a href="https://github.com/DryadeAI/dryade-plugins-sdk/actions/workflows/ci.yml"><img src="https://github.com/DryadeAI/dryade-plugins-sdk/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/dryade-plugins-sdk/"><img src="https://img.shields.io/pypi/v/dryade-plugins-sdk.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/dryade-plugins-sdk/"><img src="https://img.shields.io/pypi/pyversions/dryade-plugins-sdk.svg" alt="Python versions"></a>
  <a href="https://api.securityscorecards.dev/projects/github.com/DryadeAI/dryade-plugins-sdk"><img src="https://api.securityscorecards.dev/projects/github.com/DryadeAI/dryade-plugins-sdk/badge" alt="OpenSSF Scorecard"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://github.com/DryadeAI/dryade-plugins-sdk/discussions"><img src="https://img.shields.io/github/discussions/DryadeAI/dryade-plugins-sdk?logo=github&label=Discussions&color=5865F2" alt="Discussions"></a>
  <a href="#contributors"><img src="https://img.shields.io/badge/all_contributors-1-orange.svg" alt="All Contributors"></a>
</p>

<p align="center">
  
</p>

## Why dryade-plugins-sdk

- **Sovereign** — author plugins that ship to self-hosted Dryade installs. No cloud lock-in.
- **Type-safe** — Python `Protocol` + `@runtime_checkable`. Your IDE catches contract violations before runtime does.
- **Hermetic** — develop and test plugins without installing Dryade. The SDK ships its own test fixtures.

## Quickstart

```bash
uv tool install 'dryade-plugins-sdk[cli]'
dryade plugin new my_plugin --tier starter
cd my_plugin
dryade plugin validate
dryade plugin package
```

Five commands. Your `.dryadepkg` is ready to submit to the [Dryade marketplace](https://dryade.ai/marketplace) or share directly.

Full guide: **[dryade.ai/docs/sdk/getting-started](https://dryade.ai/docs/sdk/getting-started)**

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

- **[dryade.ai/docs/sdk/](https://dryade.ai/docs/sdk/)** — full docs site (Getting Started, Concepts, API Reference, CLI Reference, Cookbook, FAQ, Migration)
- **[Security model for authors](docs/security.md)** — what you MUST know about hashing, signing, and tier slots
- **[Contract version](docs/concepts.md#contract-version)** — current SDK `CONTRACT_VERSION` and how it gates compatibility

## Community

- **Discord** — [GitHub Discussions](https://github.com/DryadeAI/dryade-plugins-sdk/discussions) — ask questions, share what you built
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


## Publishing to the marketplace

Authoring a plugin is free. Submitting it to the Dryade marketplace is free. Where you'll see numbers:

- **Listing** — free for every tier. There is no per-listing fee.
- **Free / community plugins** — list and distribute at no cost. Author keeps full attribution; no revenue share.
- **Paid plugins** (team and enterprise tiers) — Dryade takes a **30% platform fee**; the author keeps **70%** of net (after payment processor + tax).
- **Payouts** — monthly via Stripe Connect once your accumulated balance crosses **$50**. Authors in non-Stripe geographies can opt into bank transfer at the same threshold.
- **Review SLA** — first submission: 5 business days. Updates to an already-approved plugin: 24 hours. Security patches: expedited to next business day.

The review checks: manifest validates against the v2 schema; the `.dryadepkg` is signed with a registered author key; the plugin passes the smoke test in [`examples/`](examples/); no leaks of internal Dryade symbols or credentials.

For exact terms, marketplace SLAs, or large-deal carve-outs (volume rebates, enterprise reseller, sovereign deployments): email **licensing@dryade.ai**.

## License

[MIT](LICENSE). Use it, modify it, ship it — no Dryade approval needed. See LICENSE for full terms.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->