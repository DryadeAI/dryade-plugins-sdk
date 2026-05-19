"""Dryade plugin example — ships a React UI bundle the workbench mounts.

When ``has_ui`` is true in the manifest, the workbench loads the compiled
JS bundle at ``ui/index.tsx`` (after a real build step). The host verifies
the on-disk bundle's SHA-256 matches ``ui_bundle_hash`` before mounting —
fail-closed: a tampered bundle is silently skipped.

This Python module is the **backend half** of the plugin. The UI half lives
in ``ui/index.tsx`` and is built into a single JS bundle by your toolchain
(vite / esbuild / rollup — your choice).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from dryade_plugins_sdk import HealthCheck, ManageableComponent, route


@route(path="/api/widget", method="GET", auth_required=True)
def widget_data() -> dict[str, Any]:
    """Backend endpoint the React UI fetches on mount.

    Mounted at ``/api/plugins/with_ui/api/widget`` in production. The host
    auto-injects the plugin name prefix.
    """
    return {"widget": "with_ui", "value": 42}


class WithUIPlugin:
    """Plugin that ships a React UI bundle plus a single backend route."""

    name = "with_ui"
    version = "0.1.0"
    description = "Dryade plugin example — ships a React UI bundle the workbench mounts."
    core_version_constraint = ">=1.0.0,<2.0.0"

    def register(self, registry: Any) -> None:
        registry.register(widget_data)

    def startup(self, **kwargs: Any) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def get_health_checks(self) -> Mapping[str, HealthCheck]:
        return {}

    def get_manageable_components(self) -> Iterable[ManageableComponent]:
        return []


plugin = WithUIPlugin()
