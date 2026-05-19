# multi_agent

Plugin with **two agents that collaborate via shared KV**. The
`researcher` agent gathers raw findings under a KV key; the `summarizer`
agent reads that key, compresses, and writes a summary back.

## What this example shows

- **Manifest agents block** declares two agents with distinct capabilities
  (`gather` and `compress`). The host's planner uses the capability strings
  to route tasks.
- **Shared KV** — the agents communicate without direct coupling. Each
  reads/writes under a namespaced key (`multi_agent:findings`,
  `multi_agent:summary`).
- **AgentCard + AgentCapability** — each agent advertises what it can do
  via `get_card()`, mirroring the A2A discovery pattern.
- **Late KV binding** — `register()` constructs the agents with a lazy KV
  ref; `startup(kv=host.kv)` swaps in the host-provided KV.

## Files

| File | Purpose |
|------|---------|
| `dryade.json` | Manifest declares two agents and `data:read` / `data:write` permissions |
| `plugin.py` | Two agent classes + plugin orchestration |
| `tests/test_plugin.py` | Agent registration + collaboration + failure modes |

## Run the tests

```bash
cd examples/multi_agent
pytest tests/
```

## Production notes

Real agent plugins should:

1. **Namespace KV keys** with the plugin name (we use `multi_agent:` prefix)
   to avoid collisions with other plugins sharing the host KV.
2. **Handle missing predecessor output** — see
   `test_summarizer_alone_fails_gracefully` — the summarizer reports an
   error rather than crashing when findings are absent.
3. **Use the planner's framework choice** — `framework: "crewai"` in the
   manifest tells the host to wrap calls in the CrewAI adapter. Other
   choices: `langchain`, `adk`, `a2a`, `mcp`.

The collaboration pattern (write to KV key A → read by partner →
write to key B) generalizes to N agents. Larger collaborations should
move to a dedicated message bus once the count grows past ~5.
