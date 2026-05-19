"""Shared pytest fixtures for the SDK test suite.

Includes the ``monkeypatch_module`` module-scoped fixture used by 339-08's
smoke E2E test (H7 fix — the fixture is defined here once and referenced by
name in the smoke suite, instead of inlined as a private fixture).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_plugin(tmp_path: Path) -> Path:
    """A minimal plugin directory with a single .py file for hash tests.

    Used by test_hash_conformance.py. Provides a deterministic, isolated plugin
    layout so the hash algorithm tests are reproducible.
    """
    plugin = tmp_path / "sample_plugin"
    plugin.mkdir()
    (plugin / "__init__.py").write_text("from .plugin import plugin\n")
    (plugin / "plugin.py").write_text(
        "class _P:\n"
        "    name = 'sample'\n"
        "    version = '0.1.0'\n"
        "    description = 'sample'\n"
        "    core_version_constraint = '>=1.0.0'\n"
        "    def register(self, r): pass\n"
        "plugin = _P()\n"
    )
    return plugin


@pytest.fixture(scope="module")
def monkeypatch_module(request: pytest.FixtureRequest) -> object:
    """Module-scoped monkeypatch fixture (H7 fix).

    Pytest's built-in ``monkeypatch`` is function-scoped. The 339-08 smoke E2E
    test needs a module-scoped equivalent so e.g. ``HOME`` can be set once per
    module (otherwise every test in the module would regenerate author keys).

    This fixture exposes the ``_pytest.monkeypatch.MonkeyPatch`` internal API
    but via a stable name + scope. The teardown is registered via
    ``request.addfinalizer`` so the patches are reliably undone when the
    module finishes.

    Referenced by:
      - 339-08 dryade-plugins-sdk/tests/test_smoke_e2e.py::setup_author_key
    """
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    request.addfinalizer(mp.undo)
    return mp
