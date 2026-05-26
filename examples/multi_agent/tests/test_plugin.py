"""Tests for multi_agent plugin — verifies two agents collaborate via shared KV."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from dryade_plugins_sdk import ManifestV2, Plugin  # noqa: E402
from dryade_plugins_sdk.testing import FakeHost, MockKV  # noqa: E402

from plugin import plugin  # noqa: E402


def test_plugin_satisfies_protocol() -> None:
    assert isinstance(plugin, Plugin)


def test_register_records_both_agents() -> None:
    """Both researcher and summarizer must land in registry.agents."""
    host = FakeHost()
    plugin.register(host.registry)
    assert "researcher" in host.registry.agents
    assert "summarizer" in host.registry.agents


def test_agent_cards_carry_capabilities() -> None:
    """Each agent's card must declare its capability for orchestrator routing."""
    host = FakeHost()
    plugin.register(host.registry)
    researcher_card = host.registry.agents["researcher"].get_card()
    summarizer_card = host.registry.agents["summarizer"].get_card()
    assert researcher_card.capabilities[0].name == "gather"
    assert summarizer_card.capabilities[0].name == "compress"
    assert researcher_card.framework.value == "crewai"


def test_collaboration_via_shared_kv() -> None:
    """End-to-end: researcher → KV → summarizer reproduces a real plan run."""
    host = FakeHost()
    plugin.register(host.registry)
    plugin.startup(kv=host.kv)

    researcher = host.registry.agents["researcher"]
    summarizer = host.registry.agents["summarizer"]

    # First leg
    research_result = asyncio.run(researcher.execute("entropy"))
    assert research_result.status == "ok"
    assert host.kv.get("multi_agent:findings") is not None
    assert len(host.kv.get("multi_agent:findings")) == 2

    # Second leg consumes first leg's output
    summary_result = asyncio.run(summarizer.execute("entropy"))
    assert summary_result.status == "ok"
    assert "2 findings" in summary_result.result
    assert "entropy" in summary_result.result
    # Sibling KV key populated
    assert host.kv.get("multi_agent:summary") == summary_result.result


def test_summarizer_alone_fails_gracefully() -> None:
    """Without the researcher having run, the summarizer must report no-data error."""
    plugin.register(FakeHost().registry)  # fresh agents
    fresh_kv = MockKV()
    plugin.startup(kv=fresh_kv)

    summarizer = plugin.summarizer
    assert summarizer is not None
    result = asyncio.run(summarizer.execute("anything"))
    assert result.status == "error"
    assert result.error is not None
    assert "must run first" in result.error


def test_manifest_validates_against_v2_schema() -> None:
    data = json.loads((PLUGIN_ROOT / "dryade.json").read_text())
    known_fields = ManifestV2.__dataclass_fields__
    manifest = ManifestV2(**{k: v for k, v in data.items() if k in known_fields})
    assert manifest.manifest_version == "2.0"
    assert len(manifest.agents) == 2
    assert {a["name"] for a in manifest.agents} == {"researcher", "summarizer"}
