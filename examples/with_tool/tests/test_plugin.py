"""Tests for with_tool plugin — verifies Tool registration and execution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from dryade_plugins_sdk import ManifestV2, Plugin, Tool  # noqa: E402
from dryade_plugins_sdk.testing import FakeHost  # noqa: E402

from plugin import get_current_time, plugin  # noqa: E402


def test_plugin_satisfies_protocol() -> None:
    assert isinstance(plugin, Plugin)


def test_tool_decorator_stamps_schema() -> None:
    """The @tool decorator must attach a ToolSchema with the right name."""
    assert hasattr(get_current_time, "schema")
    assert get_current_time.schema.name == "get_current_time"
    assert "ISO 8601" in get_current_time.schema.description


def test_tool_satisfies_tool_protocol() -> None:
    """The decorated function must structurally satisfy the Tool Protocol."""
    assert isinstance(get_current_time, Tool)


def test_tool_returns_iso8601() -> None:
    """Calling the tool returns a parseable ISO 8601 UTC timestamp."""
    from datetime import datetime

    result = get_current_time()
    # Should parse without raising
    parsed = datetime.fromisoformat(result)
    assert parsed.tzinfo is not None, "result must be timezone-aware UTC"


def test_register_records_tool() -> None:
    """register() must hand the tool to the host registry."""
    host = FakeHost()
    host.load(plugin)
    assert "get_current_time" in host.registry.tools, (
        f"Expected get_current_time in registry.tools, got {list(host.registry.tools)}"
    )
    host.shutdown()


def test_manifest_validates_against_v2_schema() -> None:
    data = json.loads((PLUGIN_ROOT / "dryade.json").read_text())
    known_fields = ManifestV2.__dataclass_fields__
    manifest = ManifestV2(**{k: v for k, v in data.items() if k in known_fields})
    assert manifest.manifest_version == "2.0"
    assert len(manifest.tools) == 1
    assert manifest.tools[0]["name"] == "get_current_time"
