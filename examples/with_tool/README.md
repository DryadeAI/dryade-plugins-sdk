# with_tool

Plugin that exposes one tool — a `get_current_time` callable the host LLM
can invoke via the Plugin Tool Bridge.

## What this example shows

- **`@tool` decorator** stamps a `ToolSchema` on a plain function.
- **`register(registry)`** hands the tool to the host so it shows up on the
  tool bus.
- **FakeHost** + `host.registry.tools` lets you assert in tests that the
  tool got wired without spinning up Dryade core.

## Files

| File | Purpose |
|------|---------|
| `dryade.json` | Manifest declares one tool entry |
| `plugin.py` | `@tool` + `Plugin` class wiring `register(registry)` |
| `tests/test_plugin.py` | Tool protocol + registration + execution |

## Run the tests

```bash
cd examples/with_tool
pytest tests/
```

## Adding a second tool

Decorate another function with `@tool(...)`, then in `register()`:

```python
registry.register(my_other_tool)
```

The FakeHost dispatcher keys tools by `schema.name`.
