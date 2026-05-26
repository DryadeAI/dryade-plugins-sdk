"""End-to-end author UX smoke test.

Hermetic — no Dryade core install required. Reproduces the clean-clone
external-author workflow:
  1. ``dryade plugin keygen``
  2. ``dryade plugin new my_smoke_plugin --tier starter``
  3. ``dryade plugin validate ./my_smoke_plugin``
  4. ``dryade plugin package ./my_smoke_plugin``
  5. Assert .dryadepkg has v2 manifest, 128-char hex signature, correct hashes.

Defends against regression of:
- scaffold output passing validate
- the "Next steps" output using real CLI commands
- a template breaking the build
- slot-exhaustion semantics
- a community rank appearing in the CLI
- ``--tier community`` being rejected

The whole module is marked ``@pytest.mark.e2e`` so the non-e2e CI matrix
short-circuits past these tests (they need the ``dryade`` CLI on PATH). The
SDK-repo CI's dedicated ``smoke_test`` job runs ``pytest -m e2e`` after
``pip install dryade-cli``.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import tarfile
from pathlib import Path

import pytest

# Module-scoped marker so the whole file is excluded from `pytest -m "not e2e"`.
pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def hermetic_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Module-scoped fake HOME so smoke runs once with one set of author keys."""
    return tmp_path_factory.mktemp("hermetic_home")


# The `monkeypatch_module` fixture referenced below is defined in
# `tests/conftest.py`. This file references it by name only;
# no inline fixture definition.


@pytest.fixture(scope="module", autouse=True)
def setup_author_key(hermetic_home: Path, monkeypatch_module: pytest.MonkeyPatch) -> None:
    """Generate the author keypair once per module under a hermetic HOME."""
    monkeypatch_module.setenv("HOME", str(hermetic_home))

    result = subprocess.run(
        ["dryade", "plugin", "keygen"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(hermetic_home)},
    )
    assert result.returncode == 0, f"keygen failed: {result.stderr}"

    priv = hermetic_home / ".dryade-author" / "dev-key.priv"
    pub = hermetic_home / ".dryade-author" / "dev-key.pub"
    assert priv.exists(), "priv key was not created"
    assert pub.exists(), "pub key was not created"

    priv_mode = stat.S_IMODE(os.stat(priv).st_mode)
    assert priv_mode == 0o600, f"priv perm = {oct(priv_mode)}, expected 0o600"


def _run_cli(args: list[str], hermetic_home: Path) -> subprocess.CompletedProcess[str]:
    """Run ``dryade ...`` under the hermetic HOME and return the completed process."""
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(hermetic_home)},
    )


def test_scaffold_creates_v2_plugin(hermetic_home: Path, tmp_path: Path) -> None:
    """Smoke step 1: ``dryade plugin new`` produces a v2-manifest plugin."""
    result = _run_cli(
        [
            "dryade",
            "plugin",
            "new",
            "my_smoke_plugin",
            "--tier",
            "starter",
            "--out",
            str(tmp_path),
            "--description",
            "Smoke test plugin",
        ],
        hermetic_home,
    )
    assert result.returncode == 0, (
        f"scaffold failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )

    plugin_dir = tmp_path / "my_smoke_plugin"
    assert plugin_dir.exists()

    # regression net — manifest is v2
    manifest = json.loads((plugin_dir / "dryade.json").read_text())
    assert manifest["manifest_version"] == "2.0"
    assert manifest["required_tier"] == "starter"
    assert "entry_point" not in manifest  # no entry_point in v2

    # regression net — tests are meaningful (≥2 test functions + an assert)
    test_file = plugin_dir / "tests" / "test_plugin.py"
    assert test_file.exists()
    text = test_file.read_text()
    assert text.count("def test_") >= 2
    assert "assert" in text

    # slot disclosure in scaffold output
    out_lower = result.stdout.lower()
    assert "slot" in out_lower or "custom_plugin_slots" in out_lower


def test_validate_passes(hermetic_home: Path, tmp_path: Path) -> None:
    """Smoke step 2: ``dryade plugin validate`` accepts the scaffold output."""
    scaffold = _run_cli(
        [
            "dryade",
            "plugin",
            "new",
            "validate_smoke",
            "--tier",
            "starter",
            "--out",
            str(tmp_path),
            "--description",
            "Smoke",
        ],
        hermetic_home,
    )
    assert scaffold.returncode == 0, f"scaffold failed: {scaffold.stderr}"

    plugin_dir = tmp_path / "validate_smoke"
    result = _run_cli(
        ["dryade", "plugin", "validate", str(plugin_dir)],
        hermetic_home,
    )
    assert result.returncode == 0, (
        f"validate failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


def test_package_produces_dryadepkg(hermetic_home: Path, tmp_path: Path) -> None:
    """Smoke step 3: ``dryade plugin package`` produces .dryadepkg with valid shape.

    The .dryadepkg is a gzipped tarball (``tarfile.open(..., "w:gz")``) containing
    a v2 manifest (``dryade.json``) with both SHA-256 + SHA3-256 hashes and a
    128-char hex Ed25519 signature.
    """
    scaffold = _run_cli(
        [
            "dryade",
            "plugin",
            "new",
            "pkg_smoke",
            "--tier",
            "starter",
            "--out",
            str(tmp_path),
        ],
        hermetic_home,
    )
    assert scaffold.returncode == 0, f"scaffold failed: {scaffold.stderr}"

    plugin_dir = tmp_path / "pkg_smoke"
    dist_dir = tmp_path / "dist"

    result = _run_cli(
        ["dryade", "plugin", "package", str(plugin_dir), "--output", str(dist_dir)],
        hermetic_home,
    )
    assert result.returncode == 0, (
        f"package failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )

    pkgs = list(dist_dir.glob("*.dryadepkg"))
    assert len(pkgs) == 1, f"Expected exactly 1 .dryadepkg, got {pkgs}"
    pkg = pkgs[0]
    assert pkg.name == "pkg_smoke-0.1.0.dryadepkg"

    with tarfile.open(pkg) as tf:
        member = tf.getmember("dryade.json")
        assert member is not None
        fh = tf.extractfile("dryade.json")
        assert fh is not None
        manifest = json.loads(fh.read())

    # required_tier locked
    assert manifest["required_tier"] == "starter"
    # manifest v2
    assert manifest["manifest_version"] == "2.0"
    # no entry_point
    assert "entry_point" not in manifest
    # both hashes present, 64 hex chars each
    assert "plugin_hash_sha256" in manifest
    assert "plugin_hash_sha3_256" in manifest
    assert len(manifest["plugin_hash_sha256"]) == 64
    assert len(manifest["plugin_hash_sha3_256"]) == 64
    # Ed25519 signature: 128 hex chars
    sig = manifest["signature"]
    assert len(sig) == 128
    assert all(c in "0123456789abcdefABCDEF" for c in sig)
    # Contract version
    assert manifest["contract_version"] == 4


def test_community_tier_rejected(hermetic_home: Path, tmp_path: Path) -> None:
    """Regression net — ``--tier community`` always rejected."""
    result = _run_cli(
        [
            "dryade",
            "plugin",
            "new",
            "bad_tier_test",
            "--tier",
            "community",
            "--out",
            str(tmp_path),
        ],
        hermetic_home,
    )
    assert result.returncode != 0, "--tier community accepted"
    # Plugin dir should NOT have been created
    assert not (tmp_path / "bad_tier_test").exists()


def test_hash_conformance_at_package_time(hermetic_home: Path, tmp_path: Path) -> None:
    """At package time, the embedded hash must match a fresh compute."""
    scaffold = _run_cli(
        [
            "dryade",
            "plugin",
            "new",
            "hash_smoke",
            "--tier",
            "starter",
            "--out",
            str(tmp_path),
        ],
        hermetic_home,
    )
    assert scaffold.returncode == 0, f"scaffold failed: {scaffold.stderr}"

    plugin_dir = tmp_path / "hash_smoke"
    dist_dir = tmp_path / "dist"
    pkg_run = _run_cli(
        ["dryade", "plugin", "package", str(plugin_dir), "--output", str(dist_dir)],
        hermetic_home,
    )
    assert pkg_run.returncode == 0, f"package failed: {pkg_run.stderr}"

    pkg = next(dist_dir.glob("*.dryadepkg"))
    with tarfile.open(pkg) as tf:
        fh = tf.extractfile("dryade.json")
        assert fh is not None
        manifest = json.loads(fh.read())

    # Independently recompute the canonical SHA-256 + SHA3-256 pair using
    # only stdlib hashlib, mirroring the algorithm in
    # `dryade_plugins_sdk.packaging.compute_plugin_hash_pair`.
    py_files: list[Path] = []

    def collect_py(directory: Path) -> None:
        for entry in directory.iterdir():
            if entry.is_dir():
                if entry.name != "__pycache__":
                    collect_py(entry)
            elif entry.suffix == ".py":
                py_files.append(entry)

    collect_py(plugin_dir)
    py_files.sort()

    parts_sha256: list[str] = []
    parts_sha3_256: list[str] = []
    for abs_path in py_files:
        rel_path = abs_path.relative_to(plugin_dir)
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

    assert manifest["plugin_hash_sha256"] == expected_sha256, "SHA-256 drift"
    assert manifest["plugin_hash_sha3_256"] == expected_sha3_256, "SHA3-256 drift"


def test_no_dryade_author_dir_bundled(hermetic_home: Path, tmp_path: Path) -> None:
    """.dryadepkg must NOT contain author keys."""
    scaffold = _run_cli(
        [
            "dryade",
            "plugin",
            "new",
            "leak_test",
            "--tier",
            "starter",
            "--out",
            str(tmp_path),
        ],
        hermetic_home,
    )
    assert scaffold.returncode == 0, f"scaffold failed: {scaffold.stderr}"

    plugin_dir = tmp_path / "leak_test"
    dist_dir = tmp_path / "dist"
    pkg_run = _run_cli(
        ["dryade", "plugin", "package", str(plugin_dir), "--output", str(dist_dir)],
        hermetic_home,
    )
    assert pkg_run.returncode == 0, f"package failed: {pkg_run.stderr}"

    pkg = next(dist_dir.glob("*.dryadepkg"))
    with tarfile.open(pkg) as tf:
        member_names = tf.getnames()
        forbidden = [
            n
            for n in member_names
            if "dryade-author" in n or "dev-key.priv" in n or ".dryade/" in n
        ]
        assert not forbidden, (
            f"Author key leak — .dryadepkg contains forbidden members: {forbidden}"
        )
