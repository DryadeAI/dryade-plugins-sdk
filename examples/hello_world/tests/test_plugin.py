"""Tests for hello_world plugin.

Exercises the Plugin Protocol contract via dryade_plugins_sdk.testing.FakeHost
— no Dryade core needed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from dryade_plugins_sdk import ManifestV2, Plugin  # noqa: E402
from dryade_plugins_sdk.testing import FakeHost  # noqa: E402

from plugin import plugin  # noqa: E402  -- plugin module is at PLUGIN_ROOT/plugin.py


def test_plugin_satisfies_protocol() -> None:
    """hello_world plugin must structurally satisfy the Plugin Protocol."""
    assert isinstance(plugin, Plugin), (
        f"{type(plugin).__name__} does not satisfy Plugin Protocol — "
        "check required attributes and methods."
    )


def test_plugin_metadata() -> None:
    """Required Plugin attributes must be present and well-formed."""
    assert plugin.name == "hello_world"
    assert plugin.version == "0.1.0"
    assert plugin.description.startswith("Minimal Dryade plugin")
    assert plugin.core_version_constraint.startswith(">=")


def test_manifest_validates_against_v2_schema() -> None:
    """dryade.json must validate against the v2 schema."""
    manifest_path = PLUGIN_ROOT / "dryade.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    known_fields = ManifestV2.__dataclass_fields__
    manifest = ManifestV2(**{k: v for k, v in data.items() if k in known_fields})
    assert manifest.manifest_version == "2.0"
    assert manifest.required_tier == "starter"
    assert manifest.name == "hello_world"


def test_plugin_full_lifecycle() -> None:
    """register → startup → shutdown must complete without exceptions."""
    host = FakeHost()
    host.load(plugin)
    assert plugin in host.loaded
    # hello_world registers nothing
    assert len(host.registry.tools) == 0
    assert len(host.registry.agents) == 0
    assert len(host.registry.routes) == 0
    host.shutdown()
    assert plugin not in host.loaded
