"""package command — produces .dryadepkg with v2 manifest + 128-char hex signature.

Caveat: the package command depends on the ``dryade_plugins_sdk.cli.keys`` module. The
success-path test auto-skips when that module is not yet importable. The
fail-closed test still runs without it — it asserts the package command
exits non-zero with a clear "Run keygen first" message.
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

import pytest
from dryade_plugins_sdk.cli.cli import app

_KEYS_AVAILABLE = importlib.util.find_spec("dryade_plugins_sdk.cli.keys") is not None


@pytest.mark.skipif(not _KEYS_AVAILABLE, reason="dryade_plugins_sdk.cli.keys module not available")
def test_dryadepkg_format(runner, scaffolded_plugin: Path, tmp_path, fake_author_key):
    """Successful package produces a v2-manifest .dryadepkg with 128-char hex signature."""
    sys.modules.pop("test_plugin", None)
    out = tmp_path / "dist"
    result = runner.invoke(
        app,
        ["plugin", "package", str(scaffolded_plugin), "--output", str(out)],
    )
    assert result.exit_code == 0, result.stdout
    pkg = next(out.glob("*.dryadepkg"))
    assert pkg.exists()
    with tarfile.open(pkg, "r:gz") as tf:
        member = tf.extractfile("dryade.json")
        assert member is not None
        manifest = json.loads(member.read())
        assert manifest["manifest_version"] == "2.0"
        assert manifest["required_tier"] == "starter"
        assert "signature" in manifest
        assert len(manifest["signature"]) == 128
        assert all(c in "0123456789abcdef" for c in manifest["signature"])


def test_package_fails_without_keygen(runner, scaffolded_plugin: Path, tmp_path, author_key_dir):
    """Fail-closed: package must exit non-zero when no author key exists."""
    sys.modules.pop("test_plugin", None)
    # Ensure no key exists.
    if author_key_dir.exists():
        shutil.rmtree(author_key_dir)
    out = tmp_path / "dist"
    result = runner.invoke(
        app,
        ["plugin", "package", str(scaffolded_plugin), "--output", str(out)],
    )
    assert result.exit_code != 0
    assert "keygen" in result.stdout.lower(), (
        f"package error must reference keygen; got: {result.stdout!r}"
    )


def test_no_skip_hash_or_force_flags(runner):
    """Fail-closed: --skip-hash / --force-package / --unsafe-bundle must NOT exist."""
    result = runner.invoke(app, ["plugin", "package", "--help"])
    text = result.stdout
    assert "--skip-hash" not in text
    assert "--force" not in text
    assert "--unsafe" not in text
    assert "--bypass" not in text


@pytest.mark.skipif(not _KEYS_AVAILABLE, reason="dryade_plugins_sdk.cli.keys module not available")
def test_dryadepkg_excludes_author_key_dir(
    runner, scaffolded_plugin: Path, tmp_path, fake_author_key
):
    """Bundle must NEVER include the author's private key directory."""
    sys.modules.pop("test_plugin", None)
    # Plant a stray .dryade-author/ inside the scaffold to prove EXCLUDED_PATTERNS catches it.
    stray = scaffolded_plugin / ".dryade-author"
    stray.mkdir()
    (stray / "dev-key.priv").write_bytes(b"\x00" * 32)
    out = tmp_path / "dist"
    result = runner.invoke(
        app,
        ["plugin", "package", str(scaffolded_plugin), "--output", str(out)],
    )
    assert result.exit_code == 0, result.stdout
    pkg = next(out.glob("*.dryadepkg"))
    with tarfile.open(pkg, "r:gz") as tf:
        names = tf.getnames()
        for n in names:
            assert ".dryade-author" not in n, (
                f"bundle must not include .dryade-author/; saw {n}"
            )
