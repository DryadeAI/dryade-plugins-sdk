# Examples

Five reference Dryade plugins. Each is a complete, runnable starting point —
copy any directory and edit the placeholders.

| Example | Demonstrates | Lines of Python |
|---------|--------------|-----------------|
| [`hello_world/`](hello_world/) | Minimal `Plugin` protocol skeleton | ~25 |
| [`with_tool/`](with_tool/) | Register an `@tool` the host LLM can call | ~40 |
| [`with_llm/`](with_llm/) | Tool that calls the host LLM via the Leash protocol | ~60 |
| [`with_ui/`](with_ui/) | Plugin that ships a React UI bundle (`has_ui: true`) | ~50 + UI |
| [`multi_agent/`](multi_agent/) | Two agents collaborate via shared KV | ~90 |

Directory names use snake_case because Dryade plugins ship as importable
Python packages — the dryade-cli scaffolder enforces this with
`^[a-z][a-z0-9_]{1,49}$`.

## Run an example locally

```bash
cd examples/hello_world
pytest tests/
```

To validate and package the example as a `.dryadepkg`:

```bash
uv tool install dryade-cli
cd examples/hello_world
dryade plugin validate
dryade plugin package
```

The produced `.dryadepkg` is submittable to the Dryade marketplace or shareable
directly with another Dryade install.

## Why these five

The set is chosen to cover the most common authoring patterns without
duplicating. If you build a plugin and feel one of these is missing a
common pattern, open a PR or a Discussion — examples are the front door.
