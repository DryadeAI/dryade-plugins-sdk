"""D-08 / T-339-04b-01 / T-339-04b-02 / T-339-04b-03 — keygen contract tests.

Locks down:
- ``~/.dryade-author/`` is the canonical storage path (D-08), separate from
  ``~/.dryade/``.
- Private key file is 0o600, parent dir is 0o700 (T-339-04b-02).
- Re-running keygen without ``--force`` REFUSES to overwrite (T-339-04b-01).
- ``--force`` actually rotates the bytes.
- Private key bytes never appear in stdout (T-339-04b-03).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from dryade_plugins_sdk.cli.cli import app


def test_permissions(runner, author_key_dir: Path) -> None:
    """D-08: priv key must be 0o600, dir 0o700."""
    result = runner.invoke(app, ["plugin", "keygen"])
    assert result.exit_code == 0, result.stdout
    priv = author_key_dir / "dev-key.priv"
    pub = author_key_dir / "dev-key.pub"
    assert priv.exists(), f"priv key missing at {priv}"
    assert pub.exists(), f"pub key missing at {pub}"
    priv_mode = stat.S_IMODE(os.stat(priv).st_mode)
    dir_mode = stat.S_IMODE(os.stat(author_key_dir).st_mode)
    assert priv_mode == 0o600, f"priv key perm = {oct(priv_mode)}, expected 0o600"
    assert dir_mode == 0o700, f"key dir perm = {oct(dir_mode)}, expected 0o700"


def test_keygen_refuses_overwrite(runner, author_key_dir: Path) -> None:
    """No silent rotation — keygen must refuse if key exists."""
    runner.invoke(app, ["plugin", "keygen"])
    result = runner.invoke(app, ["plugin", "keygen"])  # second call
    assert result.exit_code != 0, "keygen must exit non-zero on existing key"
    # Either "already exists" or "--force" must appear in the remediation message.
    out_lower = result.stdout.lower()
    assert "already exists" in out_lower or "--force" in out_lower, (
        f"keygen remediation must mention 'already exists' or '--force', got: {result.stdout!r}"
    )


def test_force_rotate(runner, author_key_dir: Path) -> None:
    """--force overwrites the existing key and prints a clear rotation warning."""
    runner.invoke(app, ["plugin", "keygen"])
    priv_before = (author_key_dir / "dev-key.priv").read_bytes()
    result = runner.invoke(app, ["plugin", "keygen", "--force"])
    assert result.exit_code == 0, result.stdout
    priv_after = (author_key_dir / "dev-key.priv").read_bytes()
    assert priv_before != priv_after, "key bytes did not rotate"
    assert "ROTATED" in result.stdout or "rotated" in result.stdout.lower(), (
        "force-rotate must announce the rotation"
    )


def test_keygen_separate_from_dryade_dir(runner, author_key_dir: Path) -> None:
    """D-08: ~/.dryade-author/ must NOT be the same as ~/.dryade/."""
    runner.invoke(app, ["plugin", "keygen"])
    assert author_key_dir.name == ".dryade-author", (
        f"keygen wrote to wrong directory: {author_key_dir}"
    )
    # The end-user state dir must NEVER be touched by keygen.
    home = Path.home()
    end_user_dir = home / ".dryade"
    # If the dir already existed for some reason, that's fine — but keygen
    # must not have created or modified anything under it.
    if end_user_dir.exists():
        for entry in end_user_dir.iterdir():
            assert "dev-key" not in entry.name, f"keygen leaked into end-user dir: {entry}"


def test_keygen_does_not_print_private_key(runner, author_key_dir: Path) -> None:
    """T-339-04b-03 mitigation: private key bytes never appear in stdout."""
    result = runner.invoke(app, ["plugin", "keygen"])
    assert result.exit_code == 0, result.stdout
    priv_bytes = (author_key_dir / "dev-key.priv").read_bytes()
    priv_hex = priv_bytes.hex()
    assert priv_hex not in result.stdout, (
        "T-339-04b-03 VIOLATION: private key hex appeared in stdout"
    )
    # Also assert the raw bytes (unlikely but explicit).
    assert priv_bytes.decode("latin-1") not in result.stdout, (
        "T-339-04b-03 VIOLATION: private key raw bytes appeared in stdout"
    )
