"""Tests for with_llm plugin — verifies host-LLM wiring and Leash declaration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest  # noqa: E402
from dryade_plugins_sdk import IsolationLevel, Leash, ManifestV2, Plugin  # noqa: E402
from dryade_plugins_sdk.testing import FakeHost, MockLLM  # noqa: E402

from plugin import plugin, summarize  # noqa: E402
import plugin as plugin_module  # noqa: E402  -- module reference to inspect _llm


def test_plugin_satisfies_protocol() -> None:
    assert isinstance(plugin, Plugin)


def test_leash_satisfies_protocol() -> None:
    """The plugin's leash attribute must structurally satisfy the Leash Protocol."""
    assert isinstance(plugin.leash, Leash)
    assert plugin.leash.isolation == IsolationLevel.PROCESS
    assert plugin.leash.network is True
    assert plugin.leash.memory_mb == 256


def test_summarize_raises_before_startup() -> None:
    """Calling the tool before startup wires the LLM must raise loudly."""
    # Reset the module-level cache first (other tests may have populated it).
    plugin_module._llm = None
    with pytest.raises(RuntimeError, match="before startup"):
        summarize("anything")


def test_startup_wires_host_llm() -> None:
    """startup(llm=...) must populate the module-level LLM reference."""
    plugin_module._llm = None  # reset
    fake_llm = MockLLM(responses=["A one-sentence summary."])
    plugin.startup(llm=fake_llm)
    assert plugin_module._llm is fake_llm
    plugin.shutdown()
    assert plugin_module._llm is None


def test_summarize_calls_host_llm() -> None:
    """summarize() must dispatch through the host LLM and return its response."""
    plugin_module._llm = None
    fake_llm = MockLLM(responses=["Cats are mammals."])
    plugin.startup(llm=fake_llm)

    result = summarize("Cats are small carnivorous mammals.")
    assert result == "Cats are mammals."
    assert len(fake_llm.calls) == 1
    assert "Summarize" in fake_llm.calls[0].prompt

    plugin.shutdown()


def test_register_records_tool() -> None:
    """register() puts the tool on the registry."""
    host = FakeHost()
    plugin.register(host.registry)
    assert "summarize" in host.registry.tools


def test_manifest_validates_against_v2_schema() -> None:
    data = json.loads((PLUGIN_ROOT / "dryade.json").read_text())
    known_fields = ManifestV2.__dataclass_fields__
    manifest = ManifestV2(**{k: v for k, v in data.items() if k in known_fields})
    assert manifest.manifest_version == "2.0"
    assert len(manifest.tools) == 1
    assert manifest.tools[0]["name"] == "summarize"
