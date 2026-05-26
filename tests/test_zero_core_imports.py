"""The SDK must NEVER import from core.* — enforced via AST walk."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SDK_ROOT = Path(__file__).parent.parent / "src" / "dryade_plugins_sdk"


def _collect_imports(py_file: Path) -> list[str]:
    """Return module names imported by a Python file (top-level + from-imports)."""
    tree = ast.parse(py_file.read_text(), filename=str(py_file))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


@pytest.mark.parametrize(
    "py_file",
    sorted(SDK_ROOT.rglob("*.py")),
    ids=lambda p: str(p.relative_to(SDK_ROOT)),
)
def test_no_core_imports(py_file: Path) -> None:
    """Every SDK source file must import zero ``core.*`` modules."""
    imports = _collect_imports(py_file)
    bad = [imp for imp in imports if imp == "core" or imp.startswith("core.")]
    assert not bad, (
        f"host-import violation: {py_file.relative_to(SDK_ROOT)} imports {bad!r}. "
        f"SDK must never reach into core.* — implement the protocol instead."
    )


def test_no_dryade_internal_imports() -> None:
    """No SDK file imports from the private monorepo's namespace paths."""
    all_imports: list[tuple[Path, str]] = []
    for py_file in sorted(SDK_ROOT.rglob("*.py")):
        for imp in _collect_imports(py_file):
            all_imports.append((py_file, imp))

    forbidden_prefixes = ("dryade_internal", "dryade.core", "dryade_market")
    bad: list[tuple[Path, str]] = [
        (py_file, imp)
        for py_file, imp in all_imports
        if any(imp.startswith(p) for p in forbidden_prefixes)
    ]
    assert not bad, f"host-import violation: forbidden internal-repo imports: {bad}"


def test_no_top_level_dryade_import() -> None:
    """SDK files must never `import dryade` or `from dryade import ...`.

    The package is ``dryade_plugins_sdk`` — the bare ``dryade`` namespace is
    reserved for internal modules and importing it from the SDK would leak the
    internal namespace into the public author surface.
    """
    leaks: list[tuple[Path, str]] = []
    for py_file in sorted(SDK_ROOT.rglob("*.py")):
        for imp in _collect_imports(py_file):
            if imp == "dryade" or imp.startswith("dryade."):
                leaks.append((py_file.relative_to(SDK_ROOT), imp))
    assert not leaks, f"SDK leaks internal namespace: {leaks}"
