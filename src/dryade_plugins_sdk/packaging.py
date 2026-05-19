"""Plugin packaging primitives — Rule §9 contract v4 dual hash + Ed25519 signing.

CRITICAL: ``compute_plugin_hash_pair`` MUST be byte-identical to core's
``_compute_plugin_hash_pair`` (Dryade/core/core/ee/plugin_security.ee.py:119).
Drift breaks the allowlist hash gate — plugins built with the SDK would fail
on-disk hash verification at core load time.

Tests: ``tests/test_hash_conformance.py`` independently re-computes the digest
pair from canonical bytes and asserts equality. That test is the regression net
required by Rule §9.

Algorithm v4 (must match scanner.rs::hash_plugin_files in dryade-plugin-manager
and ``_compute_plugin_hash_pair`` in core's plugin_security.ee.py):

1. Collect all *.py files recursively, excluding ``__pycache__/`` dirs and
   ``*.pyc`` files. Return absolute paths.
2. Sort the absolute paths lexicographically (the canonical ordering).
3. For each file: ``per_file_hash = H(rel_posix_path + b":" + file_bytes)``
   where rel_posix_path is the file path relative to ``plugin_dir`` with
   forward-slash separators. Compute once with H = SHA-256 and once with
   H = SHA3-256.
4. For each algorithm, build a list of ``"<rel_posix_path>:<hex_per_file>"``
   strings in the same iteration order.
5. ``"\n".join(parts).encode("utf-8")`` — no trailing newline.
6. Final digest = H over the joined bytes for each algorithm.
7. Return ``(sha256_hex, sha3_256_hex)`` — both bare lowercase hex, no
   algorithm prefix.

This module has ZERO core.* imports (D-05).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dryade_plugins_sdk.exceptions import HashMismatchError

# Plugin contract v4 — SHA-256 + SHA3-256 dual hash (Rule §9).
# Bump this constant ONLY when core's _compute_plugin_hash_pair bumps in lockstep.
CONTRACT_VERSION = 4


def _collect_py_files(plugin_dir: Path) -> list[Path]:
    """Recursively collect *.py files under ``plugin_dir``, sorted lexicographically.

    Skips ``__pycache__/`` directories and ``*.pyc`` files. Returns absolute
    paths. Matches core's ``_collect_py_files`` byte-for-byte.
    """
    py_files: list[Path] = []

    def collect_py(directory: Path) -> None:
        for entry in directory.iterdir():
            if entry.is_dir():
                if entry.name != "__pycache__":
                    collect_py(entry)
            elif entry.suffix == ".py":
                py_files.append(entry)

    collect_py(plugin_dir)
    py_files.sort()  # Sort absolute paths lexicographically
    return py_files


def compute_plugin_hash_pair(plugin_dir: Path) -> tuple[str, str]:
    """Return ``(sha256_hex, sha3_256_hex)`` for the plugin's source tree.

    The two digests are computed independently in the same iteration to
    minimize drift risk. Both are 64-char lowercase hex strings, no algorithm
    prefix. Algorithm details documented at module level.

    Args:
        plugin_dir: Path to the plugin source directory.

    Returns:
        Tuple ``(sha256_hex, sha3_256_hex)``.
    """
    py_files = _collect_py_files(plugin_dir)

    parts_sha256: list[str] = []
    parts_sha3_256: list[str] = []

    for abs_path in py_files:
        rel_path = abs_path.relative_to(plugin_dir)
        # Forward slashes for cross-platform consistency (matches Rust scanner.rs).
        rel_str = str(rel_path).replace("\\", "/")
        content = abs_path.read_bytes()

        h_sha256 = hashlib.sha256()
        h_sha256.update(rel_str.encode("utf-8"))
        h_sha256.update(b":")
        h_sha256.update(content)
        parts_sha256.append(f"{rel_str}:{h_sha256.hexdigest()}")

        h_sha3_256 = hashlib.sha3_256()
        h_sha3_256.update(rel_str.encode("utf-8"))
        h_sha3_256.update(b":")
        h_sha3_256.update(content)
        parts_sha3_256.append(f"{rel_str}:{h_sha3_256.hexdigest()}")

    combined_sha256 = "\n".join(parts_sha256).encode("utf-8")
    combined_sha3_256 = "\n".join(parts_sha3_256).encode("utf-8")
    return (
        hashlib.sha256(combined_sha256).hexdigest(),
        hashlib.sha3_256(combined_sha3_256).hexdigest(),
    )


def get_canonical_bytes(manifest_dict: dict[str, Any]) -> bytes:
    """Return canonical JSON bytes for signing.

    Rules (must match ``scripts/sign_plugins.py::_get_canonical_bytes`` semantics
    plus the workbench JS verifier's ``ensure_ascii=False`` parity rule):
      - ``sort_keys=True``
      - ``separators=(",", ":")``
      - ``ensure_ascii=False`` (parity with workbench JS verifier — Unicode is
        emitted literally rather than as ``\\uXXXX`` escape sequences)
      - Exclude BOTH ``signature`` and ``signature_pq`` fields
      - No trailing newline
    """
    canonical = {k: v for k, v in manifest_dict.items() if k not in ("signature", "signature_pq")}
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_manifest(manifest_dict: dict[str, Any], private_key: Ed25519PrivateKey) -> str:
    """Sign a manifest dict and return hex-encoded Ed25519 signature.

    Returns a 128-hex-char string (64 raw bytes, lowercase hex).
    """
    canonical_bytes = get_canonical_bytes(manifest_dict)
    sig_bytes = private_key.sign(canonical_bytes)
    return sig_bytes.hex()


def load_private_key(key_path: Path) -> Ed25519PrivateKey:
    """Load a raw 32-byte Ed25519 private key.

    Matches the format expected by ``scripts/sign_plugins.py`` — a raw 32-byte
    seed written to disk by ``cryptography.hazmat.primitives.asymmetric.ed25519
    .Ed25519PrivateKey.generate().private_bytes_raw()``.

    Args:
        key_path: Path to the private key file (canonical path:
            ``~/.dryade-author/dev-key.priv``).

    Raises:
        FileNotFoundError: if ``key_path`` does not exist.
        ValueError: if the file is not exactly 32 bytes.
    """
    if not key_path.exists():
        raise FileNotFoundError(
            f"Author key not found at {key_path}. Run `dryade plugin keygen` to generate one."
        )

    raw_bytes = key_path.read_bytes()
    if len(raw_bytes) != 32:
        raise ValueError(
            f"Expected raw 32-byte Ed25519 key, got {len(raw_bytes)} bytes at {key_path}"
        )
    return Ed25519PrivateKey.from_private_bytes(raw_bytes)


def verify_plugin_hash(plugin_dir: Path, expected_sha256: str, expected_sha3_256: str) -> None:
    """Re-compute the dual hash for ``plugin_dir`` and compare against expected.

    Args:
        plugin_dir: Path to the plugin source directory.
        expected_sha256: Expected SHA-256 hex digest.
        expected_sha3_256: Expected SHA3-256 hex digest.

    Raises:
        HashMismatchError: if either digest fails to match (Rule §9 freshness).
    """
    actual_sha256, actual_sha3_256 = compute_plugin_hash_pair(plugin_dir)
    if actual_sha256 != expected_sha256:
        raise HashMismatchError(
            f"SHA-256 mismatch — expected {expected_sha256[:16]}…, "
            f"got {actual_sha256[:16]}…. Re-package with `dryade plugin package`."
        )
    if actual_sha3_256 != expected_sha3_256:
        raise HashMismatchError(
            f"SHA3-256 mismatch — expected {expected_sha3_256[:16]}…, "
            f"got {actual_sha3_256[:16]}…. Re-package with `dryade plugin package`."
        )


__all__ = [
    "CONTRACT_VERSION",
    "compute_plugin_hash_pair",
    "get_canonical_bytes",
    "sign_manifest",
    "load_private_key",
    "verify_plugin_hash",
]
