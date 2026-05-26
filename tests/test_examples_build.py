"""Build all examples — fails CI if any example breaks against the current SDK.

Walks ``examples/*/`` and for each directory containing a ``dryade.json``:

1. Validates the manifest against the v2 JSON schema (ManifestV2 constructor).
2. Imports the example's ``plugin`` module via ``importlib`` and asserts that
   the exported ``plugin`` attribute satisfies the Plugin Protocol.
3. Runs the example's own pytest suite (`pytest examples/<name>/tests/`) in
   a subprocess so each example's local pytest config (its own
   ``pyproject.toml``) takes effect.

This is the regression net against silent breakage of examples.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from dryade_plugins_sdk import ManifestV2, Plugin

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"

EXAMPLE_DIRS = sorted(
    p for p in EXAMPLES_DIR.iterdir() if p.is_dir() and (p / "dryade.json").exists()
)


def test_examples_dir_has_expected_count() -> None:
    """We expect exactly 5 reference examples."""
    names = [p.name for p in EXAMPLE_DIRS]
    expected = {"hello_world", "with_tool", "with_llm", "with_ui", "multi_agent"}
    assert set(names) == expected, f"Examples drift: have {set(names)}, expected {expected}"


@pytest.mark.parametrize("example_dir", EXAMPLE_DIRS, ids=lambda p: p.name)
def test_example_manifest_validates(example_dir: Path) -> None:
    """Each example's dryade.json must validate against the v2 schema."""
    data = json.loads((example_dir / "dryade.json").read_text())
    known = ManifestV2.__dataclass_fields__
    manifest = ManifestV2(**{k: v for k, v in data.items() if k in known})
    assert manifest.manifest_version == "2.0"
    # no entry_point in v2
    assert "entry_point" not in data
    # only canonical tier names
    assert manifest.required_tier in {"starter", "team", "enterprise"}


@pytest.mark.parametrize("example_dir", EXAMPLE_DIRS, ids=lambda p: p.name)
def test_example_plugin_imports(example_dir: Path) -> None:
    """Each example's plugin module must import cleanly and expose `plugin`.

    Loads `plugin.py` by file path under a synthetic module name. The module
    IS registered into ``sys.modules`` (a) because ``@dataclass`` in the
    plugin body looks up the owning module via ``sys.modules[__module__]``
    and (b) under a unique synthetic name so multiple examples don't
    collide when tested back-to-back.
    """
    synthetic_name = f"_example_{example_dir.name}"
    spec = importlib.util.spec_from_file_location(
        synthetic_name,
        example_dir / "plugin.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[synthetic_name] = mod
    try:
        spec.loader.exec_module(mod)
        assert hasattr(mod, "plugin"), (
            f"{example_dir.name}/plugin.py is missing the `plugin` export"
        )
        assert isinstance(mod.plugin, Plugin), (
            f"{example_dir.name}.plugin does not satisfy Plugin Protocol"
        )
    finally:
        sys.modules.pop(synthetic_name, None)


@pytest.mark.parametrize("example_dir", EXAMPLE_DIRS, ids=lambda p: p.name)
def test_example_has_required_files(example_dir: Path) -> None:
    """Each example must ship the canonical 5-file shape."""
    required = {
        "dryade.json",
        "__init__.py",
        "plugin.py",
        "README.md",
        "pyproject.toml",
    }
    have = {p.name for p in example_dir.iterdir() if p.is_file()}
    missing = required - have
    assert not missing, f"{example_dir.name} missing required files: {missing}"

    tests_dir = example_dir / "tests"
    assert tests_dir.is_dir(), f"{example_dir.name}/tests/ is missing"
    assert (tests_dir / "test_plugin.py").exists(), (
        f"{example_dir.name}/tests/test_plugin.py is missing"
    )


@pytest.mark.parametrize("example_dir", EXAMPLE_DIRS, ids=lambda p: p.name)
def test_example_test_file_has_assertions(example_dir: Path) -> None:
    """Each example's tests must carry ≥3 real assertions."""
    test_file = example_dir / "tests" / "test_plugin.py"
    text = test_file.read_text()
    assert text.count("def test_") >= 3, (
        f"{example_dir.name}/tests/test_plugin.py has < 3 test functions"
    )
    assert text.count("assert ") >= 3, f"{example_dir.name}/tests/test_plugin.py has < 3 assertions"


@pytest.mark.parametrize("example_dir", EXAMPLE_DIRS, ids=lambda p: p.name)
def test_example_pytest_suite_passes(example_dir: Path) -> None:
    """Run each example's own pytest suite as a subprocess.

    Spawning a fresh pytest per example isolates pyproject.toml config
    (the examples set `[tool.pytest.ini_options]` for their own testpaths).
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=example_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"{example_dir.name} pytest failed (rc={result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
