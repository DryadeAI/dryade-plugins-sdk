# with_llm

Plugin that exposes a `summarize` tool which calls the host LLM. Demonstrates
how to **request outbound network via a Leash declaration** and how to
**bind the host-provided LLM at startup**.

## What this example shows

- **Leash declaration** — the plugin tells the host its isolation needs
  (`PROCESS` sandbox, `network=True`, 256 MB memory). The host honors or
  refuses at sandbox-setup time.
- **Late LLM binding** — the plugin caches a reference to the host-provided
  LLM in `startup(llm=...)`. The tool body then dispatches `_llm.complete(...)`.
- **Failure modes** — calling the tool before `startup` wires the LLM raises
  `RuntimeError`. Tests assert that contract.

## Files

| File | Purpose |
|------|---------|
| `dryade.json` | Manifest declares one tool entry + tags |
| `plugin.py` | `@tool` + `Leash` + late-bound `_llm` + `startup` wiring |
| `tests/test_plugin.py` | Tool registration + Leash protocol + LLM dispatch |

## Run the tests

```bash
cd examples/with_llm
pytest tests/
```

## Production notes

Production plugins should NOT use a module-level global for the LLM
reference — it makes the plugin un-reentrant. Use an instance attribute
on a class your tool callable closes over, or use the host's tool-execution
context (`kwargs["ctx"].llm`) once that contract is stable.

The example uses a global for clarity; the production pattern is documented
at `docs/cookbook.md`.
