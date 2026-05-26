"""Contract v4: SDK ``compute_plugin_hash_pair`` MUST be byte-identical to the
host runtime's plugin-hash algorithm.

This test independently recomputes both digests using only stdlib ``hashlib``
and asserts equality with the SDK function's output. If the SDK drifts from
the host's algorithm, this test catches it before plugins built with the SDK
fail the host's on-disk hash gate.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from dryade_plugins_sdk.packaging import CONTRACT_VERSION, compute_plugin_hash_pair


def test_contract_version_is_four() -> None:
    """SDK must declare contract v4 (SHA-256 + SHA3-256 dual hash)."""
    assert CONTRACT_VERSION == 4


def test_hash_pair_matches_canonical_algorithm(sample_plugin: Path) -> None:
    """SDK hash matches the canonical algorithm byte-for-byte."""
    sha256_hex, sha3_256_hex = compute_plugin_hash_pair(sample_plugin)

    # Independent re-computation using only stdlib hashlib, mirroring the
    # canonical host algorithm.
    py_files: list[Path] = []

    def collect_py(directory: Path) -> None:
        for entry in directory.iterdir():
            if entry.is_dir():
                if entry.name != "__pycache__":
                    collect_py(entry)
            elif entry.suffix == ".py":
                py_files.append(entry)

    collect_py(sample_plugin)
    py_files.sort()

    parts_sha256: list[str] = []
    parts_sha3_256: list[str] = []
    for abs_path in py_files:
        rel_path = abs_path.relative_to(sample_plugin)
        rel_str = str(rel_path).replace("\\", "/")
        content = abs_path.read_bytes()
        per_file_sha256 = hashlib.sha256()
        per_file_sha256.update(rel_str.encode("utf-8"))
        per_file_sha256.update(b":")
        per_file_sha256.update(content)
        per_file_sha3_256 = hashlib.sha3_256()
        per_file_sha3_256.update(rel_str.encode("utf-8"))
        per_file_sha3_256.update(b":")
        per_file_sha3_256.update(content)
        parts_sha256.append(f"{rel_str}:{per_file_sha256.hexdigest()}")
        parts_sha3_256.append(f"{rel_str}:{per_file_sha3_256.hexdigest()}")
    expected_sha256 = hashlib.sha256("\n".join(parts_sha256).encode("utf-8")).hexdigest()
    expected_sha3_256 = hashlib.sha3_256("\n".join(parts_sha3_256).encode("utf-8")).hexdigest()

    assert sha256_hex == expected_sha256, "SHA-256 drift from canonical algorithm"
    assert sha3_256_hex == expected_sha3_256, "SHA3-256 drift from canonical algorithm"


def test_hash_changes_on_file_edit(sample_plugin: Path) -> None:
    """Editing a .py file invalidates both digests (hash freshness)."""
    sha256_before, sha3_before = compute_plugin_hash_pair(sample_plugin)
    target = sample_plugin / "plugin.py"
    target.write_text(target.read_text() + "\n# edit\n")
    sha256_after, sha3_after = compute_plugin_hash_pair(sample_plugin)
    assert sha256_before != sha256_after
    assert sha3_before != sha3_after


def test_hash_sorted_deterministic(sample_plugin: Path) -> None:
    """Hash output is deterministic given the same input."""
    h1 = compute_plugin_hash_pair(sample_plugin)
    h2 = compute_plugin_hash_pair(sample_plugin)
    assert h1 == h2


def test_hash_ignores_pycache(sample_plugin: Path) -> None:
    """``__pycache__/`` dirs and ``*.pyc`` files MUST be excluded from the hash.

    The canonical algorithm explicitly skips ``__pycache__`` directories.
    """
    sha256_before, sha3_before = compute_plugin_hash_pair(sample_plugin)
    # Drop a fake bytecode cache that should NOT affect the hash.
    pycache = sample_plugin / "__pycache__"
    pycache.mkdir()
    (pycache / "plugin.cpython-311.pyc").write_bytes(b"\x00\x01\x02FAKE")
    sha256_after, sha3_after = compute_plugin_hash_pair(sample_plugin)
    assert sha256_before == sha256_after
    assert sha3_before == sha3_after


def test_hash_returns_hex_pair(sample_plugin: Path) -> None:
    """Both elements of the pair are 64-char lowercase hex strings (no algorithm prefix)."""
    sha256_hex, sha3_256_hex = compute_plugin_hash_pair(sample_plugin)
    assert len(sha256_hex) == 64
    assert len(sha3_256_hex) == 64
    assert all(c in "0123456789abcdef" for c in sha256_hex)
    assert all(c in "0123456789abcdef" for c in sha3_256_hex)
    # Bare hex — no "sha256:" / "sha3-256:" prefix.
    assert ":" not in sha256_hex
    assert ":" not in sha3_256_hex
