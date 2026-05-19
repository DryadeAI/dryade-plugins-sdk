# Examples

Five reference plugins live under
[`examples/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples)
in the repo. Each is a complete, runnable starting point — copy any
directory and edit the placeholders.

## hello_world

[`examples/hello_world/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples/hello_world)

The smallest possible plugin. Satisfies the `Plugin` Protocol with the
absolute minimum: required attributes, a `register` method that does
nothing, and stub lifecycle hooks. ~25 lines of Python.

Use this as the template for a plugin that contributes nothing at boot but
sets up infrastructure (e.g. health-check-only plugins).

## with_tool

[`examples/with_tool/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples/with_tool)

Exposes one tool — `get_current_time` — the host LLM can call via the
Plugin Tool Bridge. Shows the `@tool` decorator, `registry.register`
fan-out, and `FakeHost.registry.tools` assertions in tests. ~40 lines.

## with_llm

[`examples/with_llm/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples/with_llm)

Tool that calls the host LLM via the `Leash` protocol. Demonstrates the
late LLM binding pattern (`startup(llm=...)`) and a declarative sandbox
policy (`isolation=PROCESS`, `network=True`, `memory_mb=256`). ~60 lines.

## with_ui

[`examples/with_ui/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples/with_ui)

Plugin that ships a React UI bundle. Manifest declares `has_ui: true` +
`ui_bundle_hash` (SHA-256 of the compiled bundle). The host verifies the
hash before mounting the UI — fail-closed if tampered. ~50 lines of Python
+ a tiny `ui/index.tsx`.

## multi_agent

[`examples/multi_agent/`](https://github.com/DryadeAI/dryade-plugins-sdk/tree/main/examples/multi_agent)

Two agents collaborate via shared KV. The `researcher` writes findings;
the `summarizer` reads them and writes a summary back under a sibling key.
~90 lines.

## Running an example locally

```bash
git clone https://github.com/DryadeAI/dryade-plugins-sdk
cd dryade-plugins-sdk/examples/hello_world
uv pip install -e ".[testing]"
pytest tests/
```

To validate + package an example:

```bash
uv tool install dryade-cli
cd examples/hello_world
dryade plugin validate
dryade plugin package
```

## CI safety net

The repo's `tests/test_examples_build.py` builds every example on every
PR — manifest validation, plugin import, file shape check, and a
full pytest-subprocess run. T-09-3 mitigation: examples cannot silently
break.

## Submitting a new example

Examples are the documentation surface most authors will copy from. If
your plugin demonstrates a pattern not covered here, please open a PR.
The bar:

- Complete + runnable from a clean clone.
- Tests with ≥3 meaningful assertions (`pytest` from cwd green).
- Manifest validates against the v2 schema.
- README ≤30 lines.
- No host-runtime imports.

See [CONTRIBUTING.md](https://github.com/DryadeAI/dryade-plugins-sdk/blob/main/CONTRIBUTING.md)
for the PR flow.
