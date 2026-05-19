# Cookbook

Patterns we have seen plugin authors reach for. Each recipe is
copy-pasteable into `plugin.py`.

## 1. HITL prompt — pause for human approval

Sometimes an agent must pause until a human approves a side-effect (send
email, push to prod, charge a card). Use the host's HITL channel:

```python
from dryade_plugins_sdk import tool


@tool(
    name="propose_email_send",
    description="Draft an email and pause for human approval before sending.",
)
async def propose_email_send(*, to: str, subject: str, body: str) -> dict:
    from dryade_plugins_sdk.channels import await_human_approval  # host-injected

    decision = await await_human_approval(
        prompt=f"Send '{subject}' to {to}?",
        body=body,
        ttl_seconds=600,
    )
    if decision != "approve":
        return {"status": "rejected", "decision": decision}
    # ... actually send ...
    return {"status": "sent"}
```

The host renders the prompt in the workbench HITL panel; the function
suspends until the user clicks approve / reject / extend. Default TTL is
configurable via `DRYADE_HITL_TTL_S`.

## 2. MCP tool — expose your plugin's tool to MCP clients

If your plugin declares an `mcp_server` block in `dryade.json`, the host
spawns the MCP server subprocess and proxies tool calls:

```json
{
  "mcp_server": {
    "name": "my-mcp-server",
    "command": ["python", "-m", "my_plugin.mcp_server"],
    "args": [],
    "env": {"LOG_LEVEL": "info"}
  }
}
```

The `command` runs inside the plugin's Leash sandbox. Stdin/stdout speak
the MCP JSON-RPC protocol. See the official MCP spec for the on-wire shape.

## 3. Multi-agent collaboration

See [`examples/multi_agent`](examples.md#multi_agent). The pattern:
namespace KV keys by plugin name (`<plugin>:<key>`), so cross-plugin
collisions are impossible.

## 4. Persistent KV — TTL-aware caching

```python
class CachingPlugin:
    name = "caching"
    version = "0.1.0"
    description = "Caches expensive computation in plugin-local KV."
    core_version_constraint = ">=1.0.0,<2.0.0"

    def __init__(self):
        self._kv = None

    def register(self, registry): pass

    def startup(self, **kwargs):
        self._kv = kwargs.get("kv")

    @tool(name="expensive_op", description="Cached compute.")
    def expensive_op(self, key: str) -> dict:
        cached = self._kv.get(f"caching:result:{key}")
        if cached is not None:
            return cached
        result = self._compute(key)
        self._kv.set(f"caching:result:{key}", result, ttl_seconds=3600)
        return result
```

## 5. UI component — react to backend state

The UI half of a plugin (`has_ui: true`) is a React bundle the workbench
mounts. The bundle fetches from `/api/plugins/<your_plugin>/...` to talk
to your backend. Authentication / theming / toasts come from a peer
`@dryade/workbench-sdk` package — your bundle does not bundle React.

See [`examples/with_ui`](examples.md#with_ui).

## 6. Error boundary — fail-closed inside a tool

The Plugin Protocol does not give you a try/except wrapper at the tool
layer — the host catches `AgentExecutionError`. If your tool can fail in
recoverable ways, swallow at the source:

```python
@tool(name="fetch_url", description="GET a URL, surface errors as data.")
def fetch_url(url: str) -> dict:
    import requests
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return {"ok": True, "data": resp.text}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}
```

Returning `{"ok": False, ...}` lets the orchestrator make a decision; a
raised exception triggers retry/abort policy at the host.

## 7. Health check — surface plugin-internal liveness

```python
from dryade_plugins_sdk import HealthCheck


def _db_ping() -> dict:
    # ... your DB ping ...
    return {"latency_ms": 12}


class WithHealth:
    name = "with_health"
    # ... required Plugin fields ...
    def get_health_checks(self):
        return {
            "db_reachable": HealthCheck(
                name="db_reachable",
                category="critical",
                check_fn=_db_ping,
                description="Plugin DB ping",
                timeout_seconds=2.0,
            ),
        }
```

The host polls these on its own schedule, surfaces results in the
workbench, and routes to alerting if `category=critical` fails.
