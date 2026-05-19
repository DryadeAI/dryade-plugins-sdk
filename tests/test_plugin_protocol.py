"""F3.1: Plugin Protocol must be @runtime_checkable so loader's isinstance check works.

Core's plugin loader at ``plugins_ee.py:434`` calls ``isinstance(plugin, PluginProtocol)``
to verify a discovered plugin module exports a conforming object. This only works
when the Protocol is decorated with ``@runtime_checkable``.
"""

from __future__ import annotations

import typing

from dryade_plugins_sdk import Plugin


def test_plugin_is_protocol() -> None:
    """Plugin must inherit from ``typing.Protocol``."""
    assert typing.Protocol in Plugin.__mro__


def test_plugin_runtime_checkable() -> None:
    """Plugin must be decorated with ``@runtime_checkable``.

    Protocols carrying the decorator expose a private
    ``_is_runtime_protocol`` attribute set to True. See RESEARCH.md Pitfall 3
    and core/ee/plugins_ee.py:434.
    """
    assert getattr(Plugin, "_is_runtime_protocol", False), (
        "Plugin must be decorated with @runtime_checkable"
    )


def test_isinstance_works_on_conforming_object() -> None:
    """``isinstance(obj, Plugin)`` returns True for an object satisfying the Protocol."""

    class _ConformingPlugin:
        name = "x"
        version = "0.1.0"
        description = "test"
        core_version_constraint = ">=1.0.0"

        def register(self, registry: object) -> None:
            return None

        def startup(self, **kwargs: object) -> None:
            return None

        def shutdown(self) -> None:
            return None

        def get_health_checks(self) -> dict[str, object]:
            return {}

        def get_manageable_components(self) -> list[object]:
            return []

    assert isinstance(_ConformingPlugin(), Plugin)


def test_isinstance_fails_on_nonconforming() -> None:
    """``isinstance`` returns False when required attributes are missing."""

    class _Broken:
        name = "x"
        # Missing version / description / core_version_constraint / register.

    assert not isinstance(_Broken(), Plugin)
