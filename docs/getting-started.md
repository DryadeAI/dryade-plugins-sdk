# Getting Started

A five-step tour from zero to a packaged `.dryadepkg`. ~5 minutes if you
have Python 3.11+ and `uv` already installed.

## 1. Install the CLI

```bash
uv tool install dryade-cli
```

Verify:

```bash
dryade --version
```

If you do not have `uv`, install it first:
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

`pip install dryade-cli` works too — `uv tool install` is the recommended
path because it isolates the CLI in its own venv.

## 2. Generate author keys

The CLI signs your plugin package with an Ed25519 dev key. Generate it once:

```bash
dryade plugin keygen
```

This writes `~/.dryade-author/dev-key.priv` (mode `0o600`) and
`~/.dryade-author/dev-key.pub`. The marketplace consumes the public half
when you submit a plugin.

## 3. Scaffold a new plugin

```bash
dryade plugin new my_plugin --tier starter
```

You get a complete plugin directory:

```
my_plugin/
├── dryade.json           manifest v2.0
├── __init__.py           exports `plugin`
├── plugin.py             your Plugin Protocol implementation
├── pyproject.toml        Hatch build config
├── README.md             plugin docs
└── tests/
    └── test_plugin.py    7 meaningful tests (Plugin Protocol conformance,
                          manifest validation, lifecycle hooks)
```

## 4. Write + test your plugin

```bash
cd my_plugin
uv pip install -e ".[testing]"
pytest tests/
```

All 7 scaffolded tests should pass. Now edit `plugin.py` to add your
behavior. The SDK ships test fixtures
(`from dryade_plugins_sdk.testing import FakeHost, MockKV, MockLLM`) so you
can `pytest` end-to-end without installing Dryade core.

## 5. Validate + package

```bash
dryade plugin validate
dryade plugin package
```

`validate` checks the manifest schema, plugin Protocol conformance, hash
algorithm, and tier slot rules. `package` produces `my_plugin-0.1.0.dryadepkg`
— a gzipped tar archive with the manifest, signed source hashes, and your
Python files. Submit that to the marketplace or share directly with a
Dryade install.

## Next

- **[Concepts](concepts.md)** — what's a Protocol, why type-safe, what's
  contract v4.
- **[Examples](examples.md)** — 5 reference plugins covering the most
  common patterns.
- **[Cookbook](cookbook.md)** — recipes for HITL, MCP tools, multi-agent,
  KV, and UI.
