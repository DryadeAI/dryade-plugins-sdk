"""Tests for with_ui plugin — verifies route registration and UI manifest fields."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from dryade_plugins_sdk import ManifestV2, Plugin, Route  # noqa: E402
from dryade_plugins_sdk.testing import FakeHost  # noqa: E402

from plugin import plugin, widget_data  # noqa: E402


def test_plugin_satisfies_protocol() -> None:
    assert isinstance(plugin, Plugin)


def test_route_decorator_stamps_spec() -> None:
    """The @route decorator must attach a RouteSpec."""
    assert hasattr(widget_data, "spec")
    assert widget_data.spec.path == "/api/widget"
    assert widget_data.spec.method == "GET"
    assert widget_data.spec.auth_required is True


def test_route_satisfies_route_protocol() -> None:
    assert isinstance(widget_data, Route)


def test_route_callable() -> None:
    """Calling the route handler returns a JSON-serializable dict."""
    result = widget_data()
    assert result == {"widget": "with_ui", "value": 42}


def test_register_records_route() -> None:
    """register() puts the route on the registry under its path."""
    host = FakeHost()
    host.load(plugin)
    assert "/api/widget" in host.registry.routes
    host.shutdown()


def test_manifest_validates_has_ui() -> None:
    """has_ui=true requires ui_bundle_hash — schema enforces this."""
    data = json.loads((PLUGIN_ROOT / "dryade.json").read_text())
    known_fields = ManifestV2.__dataclass_fields__
    manifest = ManifestV2(**{k: v for k, v in data.items() if k in known_fields})
    assert manifest.manifest_version == "2.0"
    assert manifest.has_ui is True
    # Schema rule: has_ui=true => ui_bundle_hash required + 64-char hex SHA-256
    assert manifest.ui_bundle_hash is not None
    assert len(manifest.ui_bundle_hash) == 64
    assert all(c in "0123456789abcdef" for c in manifest.ui_bundle_hash)


def test_ui_entry_file_exists() -> None:
    """The ui/index.tsx referenced by the manifest must exist on disk."""
    ui_entry = PLUGIN_ROOT / "ui" / "index.tsx"
    assert ui_entry.exists(), f"manifest declares ui.entry but {ui_entry} is missing"
