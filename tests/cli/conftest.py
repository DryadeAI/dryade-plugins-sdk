"""Shared pytest fixtures for dryade-cli tests.

Hermetic by default — every fixture redirects HOME to tmp_path so author
keys / config files never leak into the developer's real ~/.dryade-author.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from dryade_plugins_sdk.cli.cli import app
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """typer.testing CliRunner for invoking the dryade app in-process."""
    return CliRunner()


@pytest.fixture
def author_key_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ``HOME`` to tmp_path so ~/.dryade-author lives under tmp_path.

    Returns the path the dev key WOULD live at (~/.dryade-author). Tests that
    need the key pre-populated must write to ``author_key_dir / "dev-key.priv"``.
    Tests that want to assert "no key" simply leave the directory absent.
    """
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home / ".dryade-author"


def _write_fake_author_key(author_key_dir: Path) -> Path:
    """Write a raw 32-byte Ed25519 key into ``author_key_dir / dev-key.priv``.

    339-04b ships ``dryade plugin keygen`` which writes the real key. While
    that command is not yet available (this plan ships 04a only), we fabricate
    a deterministic key so tests can exercise the package signing flow.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    author_key_dir.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    raw = key.private_bytes_raw()
    assert len(raw) == 32
    priv_path = author_key_dir / "dev-key.priv"
    priv_path.write_bytes(raw)
    priv_path.chmod(0o600)
    return priv_path


@pytest.fixture
def fake_author_key(author_key_dir: Path) -> Path:
    """Pre-populate the redirected ~/.dryade-author/dev-key.priv with a real key."""
    return _write_fake_author_key(author_key_dir)


@pytest.fixture
def scaffolded_plugin(
    tmp_path: Path,
    runner: CliRunner,
    author_key_dir: Path,
) -> Path:
    """Fresh ``dryade plugin new`` output ready for validate / package tests.

    Generates a starter-tier scaffold at ``tmp_path / "test_plugin"``. Does NOT
    pre-generate the author key — tests that need a key call ``fake_author_key``
    explicitly. (339-04b's keygen subcommand isn't shipped yet; this design lets
    the test suite work in 04a-only state.)
    """
    out_dir = tmp_path
    result = runner.invoke(
        app,
        [
            "plugin",
            "new",
            "test_plugin",
            "--tier",
            "starter",
            "--out",
            str(out_dir),
            "--description",
            "scaffold fixture",
            "--author",
            "Test Author",
        ],
    )
    assert result.exit_code == 0, f"scaffold failed: {result.stdout}\n{result.exception}"
    return out_dir / "test_plugin"
