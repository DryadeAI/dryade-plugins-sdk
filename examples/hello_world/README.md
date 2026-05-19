# hello_world

The simplest possible Dryade plugin. Satisfies the `Plugin` Protocol with
the absolute minimum: required attributes, a `register` method that does
nothing, and stub lifecycle hooks.

## Files

| File | Purpose |
|------|---------|
| `dryade.json` | Manifest v2.0 — declares plugin identity and tier |
| `plugin.py` | The `Plugin` Protocol implementation |
| `__init__.py` | Exports `plugin` for the host loader |
| `tests/test_plugin.py` | Protocol + lifecycle + manifest tests |
| `pyproject.toml` | Hatch build config |

## Run the tests

```bash
cd examples/hello_world
pytest tests/
```

## Copy this template

Start a new plugin from this skeleton, or use the scaffolder for guided
new-plugin creation:

```bash
dryade plugin new my_new_plugin --tier starter
```
