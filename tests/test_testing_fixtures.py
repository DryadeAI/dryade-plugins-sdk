"""SDK testing fixtures must work without the host runtime installed.

These tests exercise the in-memory fixtures so authors can pytest their plugins
in a clean venv that has only ``dryade-plugins-sdk`` installed.
"""

from __future__ import annotations


def test_fake_host_load_plugin() -> None:
    """``FakeHost`` accepts a Plugin and calls register/startup."""
    from dryade_plugins_sdk.testing import FakeHost

    class _Plugin:
        name = "x"
        version = "0.1.0"
        description = "test"
        core_version_constraint = ">=1.0.0"
        registered = False
        started = False

        def register(self, registry: object) -> None:
            self.registered = True

        def startup(self, **kwargs: object) -> None:
            self.started = True

        def shutdown(self) -> None:
            return None

        def get_health_checks(self) -> dict[str, object]:
            return {}

        def get_manageable_components(self) -> list[object]:
            return []

    plugin = _Plugin()
    host = FakeHost()
    host.load(plugin)
    assert plugin.registered
    assert plugin.started


def test_fake_host_dispatches_tools_and_agents() -> None:
    """FakeRegistry routes register() calls into the right bucket by attribute shape."""
    from dryade_plugins_sdk.testing import FakeHost, build_agent, build_plugin, build_tool

    host = FakeHost()
    plugin = build_plugin(
        on_register=lambda r: [
            r.register(build_tool("greet", "say hi")),
            r.register(build_agent("research", "search")),
        ]
    )
    host.load(plugin)
    assert "greet" in host.registry.tools
    assert "research" in host.registry.agents


def test_mock_kv_basic_set_get_has_delete() -> None:
    """MockKV satisfies the KV Protocol contract for the four core methods."""
    from dryade_plugins_sdk.testing import MockKV

    kv = MockKV()
    kv.set("foo", 42)
    assert kv.get("foo") == 42
    assert kv.has("foo")
    assert kv.delete("foo") is True
    assert not kv.has("foo")
    assert kv.delete("foo") is False  # second delete is a no-op


def test_mock_kv_keys_prefix() -> None:
    """``keys(prefix=...)`` filters by prefix."""
    from dryade_plugins_sdk.testing import MockKV

    kv = MockKV()
    kv.set("user:1", "a")
    kv.set("user:2", "b")
    kv.set("doc:1", "c")
    user_keys = sorted(kv.keys("user:"))
    assert user_keys == ["user:1", "user:2"]


def test_mock_config_patch_shortcut() -> None:
    """``MockConfig.patch({"key": value})`` updates the implicit ``__caller__`` namespace."""
    from dryade_plugins_sdk.testing import MockConfig

    config = MockConfig()
    config.patch({"theme": "dark", "lang": "en"})
    settings = config.get()
    assert settings["theme"] == "dark"
    assert settings["lang"] == "en"


def test_mock_llm_records_and_replays() -> None:
    """MockLLM records every call and cycles through scripted responses."""
    from dryade_plugins_sdk.testing import MockLLM

    llm = MockLLM(responses=["a", "b"])
    assert llm.complete("hello") == "a"
    assert llm.complete("again") == "b"
    assert llm.complete("once more") == "a"  # cycles
    assert len(llm.calls) == 3
    assert [c.prompt for c in llm.calls] == ["hello", "again", "once more"]
    llm.reset()
    assert llm.calls == []


def test_testing_module_has_zero_core_imports() -> None:
    """The testing subpackage itself never imports core (hermetic)."""
    import ast
    from pathlib import Path

    import dryade_plugins_sdk.testing as testing_pkg

    pkg_dir = Path(testing_pkg.__file__).parent
    for py in pkg_dir.rglob("*.py"):
        tree = ast.parse(py.read_text(), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not (node.module == "core" or node.module.startswith("core.")), (
                    f"host-import violation in {py}: from {node.module}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not (alias.name == "core" or alias.name.startswith("core.")), (
                        f"host-import violation in {py}: import {alias.name}"
                    )


def test_factories_build_plugin_conforms_to_protocol() -> None:
    """build_plugin() returns an object satisfying the Plugin Protocol structurally."""
    from dryade_plugins_sdk import Plugin
    from dryade_plugins_sdk.testing import build_plugin

    p = build_plugin(name="probe")
    assert isinstance(p, Plugin)
    assert p.name == "probe"
