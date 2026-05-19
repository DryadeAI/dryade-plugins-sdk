"""Author key management.

D-08: keys live at ``~/.dryade-author/`` (NOT ``~/.dryade/`` — end-user state).
Format: raw 32-byte Ed25519 (matches ``scripts/sign_plugins.py:99-109``).
Perms: priv key 0o600, parent dir 0o700.

Consumed by:
- ``dryade_plugins_sdk.cli.pkg.build_dryadepkg`` (via ``load_author_private_key``, lazy import)
- ``dryade_plugins_sdk.cli.commands.keygen`` (via ``generate_author_keypair``)
- ``dryade_plugins_sdk.cli.commands.package`` (via ``AUTHOR_KEY_PRIV`` existence check)
"""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# D-08 storage path. The author dev key lives under ~/.dryade-author/ — a
# DIFFERENT directory from ~/.dryade/ which is reserved for end-user PM
# state (license, allowlist, pubkey TOFU). Mixing these would let a stray
# `pip install dryade-cli` leak the dev key into the end-user runtime
# directory and vice-versa.
#
# These module-level constants document the canonical path layout for D-08.
# They are computed once at import time. Production CLI invocations run in
# a fresh process where HOME does not move, so the constants resolve
# correctly. The internal helper `_author_paths()` is used inside this
# module's functions instead, so monkeypatch-HOME-per-test still works
# correctly in a long-lived pytest session (where the constants would
# otherwise freeze against the first test's HOME).
AUTHOR_KEY_DIR = Path.home() / ".dryade-author"
AUTHOR_KEY_PRIV = AUTHOR_KEY_DIR / "dev-key.priv"
AUTHOR_KEY_PUB = AUTHOR_KEY_DIR / "dev-key.pub"


def _author_paths() -> tuple[Path, Path, Path]:
    """Resolve ``(dir, priv, pub)`` paths against the CURRENT ``Path.home()``.

    Re-evaluated on every call so that test suites which monkeypatch ``HOME``
    per-test see the right tmp_path. Module-level constants stay as the
    documented surface (per plan acceptance criteria) but functions inside
    this module use the fresh-resolution helper.
    """
    d = Path.home() / ".dryade-author"
    return d, d / "dev-key.priv", d / "dev-key.pub"


def generate_author_keypair(force: bool = False) -> tuple[str, str]:
    """Generate ``~/.dryade-author/dev-key.{priv,pub}``.

    Args:
        force: when False, refuse to overwrite an existing key. When True,
            rotate the key (callers must warn the author that prior plugin
            signatures are now invalid).

    Returns:
        ``(priv_hex, pub_hex)`` — both hex-encoded. Callers MUST NOT print
        ``priv_hex`` (T-339-04b-03 mitigation). The return is exposed only so
        tests can assert the private bytes never reached stdout.

    Raises:
        FileExistsError: when the priv key already exists and force is False.
    """
    key_dir, key_priv, key_pub = _author_paths()
    # Lock parent dir 0o700 — both on first creation and (defensively) on
    # every subsequent invocation, in case a previous run created the dir
    # with a relaxed umask.
    key_dir.mkdir(mode=0o700, exist_ok=True)
    key_dir.chmod(0o700)

    if key_priv.exists() and not force:
        raise FileExistsError(
            f"Author key already exists at {key_priv}.\n"
            "Re-run with --force to rotate (this WILL invalidate prior plugin signatures)."
        )

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    key_priv.write_bytes(priv_bytes)
    key_priv.chmod(0o600)
    key_pub.write_text(pub_bytes.hex())
    return priv_bytes.hex(), pub_bytes.hex()


def load_author_private_key() -> Ed25519PrivateKey:
    """Load the author's private key from ``~/.dryade-author/dev-key.priv``.

    Raises:
        FileNotFoundError: with a remediation pointing the author at
            ``dryade plugin keygen`` when the key is absent.
        ValueError: when the on-disk bytes are not a raw 32-byte Ed25519 key
            (matches ``scripts/sign_plugins.py:99-109`` format constraint).
    """
    _, key_priv, _ = _author_paths()
    if not key_priv.exists():
        raise FileNotFoundError(
            f"Author key not found at {key_priv}.\nRun `dryade plugin keygen` first."
        )
    raw = key_priv.read_bytes()
    if len(raw) != 32:
        raise ValueError(f"Expected raw 32-byte Ed25519 key, got {len(raw)} bytes at {key_priv}")
    return Ed25519PrivateKey.from_private_bytes(raw)


def get_author_pubkey_hex() -> str:
    """Read the hex-encoded author public key.

    Raises:
        FileNotFoundError: when ``dev-key.pub`` is missing (run keygen first).
    """
    _, _, key_pub = _author_paths()
    if not key_pub.exists():
        raise FileNotFoundError(f"No author pubkey found at {key_pub}")
    return key_pub.read_text().strip()
