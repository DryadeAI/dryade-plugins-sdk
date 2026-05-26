"""The signature on a produced .dryadepkg must verify against the author key.

Regression net for the packaging bug where the manifest was signed *before*
the ``sbom`` field was added, leaving that field outside the signed canonical
bytes so the signature failed to verify on the produced package. The signature
must cover the FINAL manifest — every content field included.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from dryade_plugins_sdk.packaging import get_canonical_bytes


@pytest.fixture
def plugin_dir(tmp_path: Path) -> Path:
    pdir = tmp_path / "sigproof"
    pdir.mkdir()
    (pdir / "dryade.json").write_text(
        json.dumps(
            {
                "manifest_version": "2.0",
                "name": "sigproof",
                "version": "0.1.0",
                "description": "Signature test fixture.",
                "core_version_constraint": ">=1.0.0,<2.0.0",
                "required_tier": "starter",
            },
            indent=2,
        )
    )
    (pdir / "__init__.py").write_text("from .plugin import plugin\n")
    (pdir / "plugin.py").write_text(
        "class Plugin:\n"
        "    name='sigproof'\n"
        "    version='0.1.0'\n"
        "    description='proof'\n"
        "    core_version_constraint='>=1.0.0,<2.0.0'\n"
        "    def register(self, r): pass\n"
        "plugin = Plugin()\n"
    )
    (pdir / "pyproject.toml").write_text(
        '[project]\nname = "sigproof"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n'
    )
    return pdir


def _packaged_manifest(monkeypatch, plugin_dir: Path, tmp_path: Path) -> tuple[dict, str]:
    """Package the plugin in an isolated $HOME; return (manifest, pubkey_hex)."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    from dryade_plugins_sdk.cli import keys

    _, pub_hex = keys.generate_author_keypair()

    from dryade_plugins_sdk.cli.pkg import build_dryadepkg

    pkg_path = build_dryadepkg(plugin_dir, tmp_path / "dist")
    with tarfile.open(pkg_path, "r:gz") as tf:
        member = tf.extractfile("dryade.json")
        assert member is not None
        manifest = json.loads(member.read().decode("utf-8"))
    return manifest, pub_hex


def test_packaged_signature_verifies(monkeypatch, plugin_dir, tmp_path):
    """The Ed25519 signature in the .dryadepkg verifies against the author key."""
    manifest, pub_hex = _packaged_manifest(monkeypatch, plugin_dir, tmp_path)

    assert manifest.get("signature"), "package has no signature"
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
    # Must not raise — the signature covers the final manifest.
    pub.verify(bytes.fromhex(manifest["signature"]), get_canonical_bytes(manifest))


def test_signature_covers_sbom_field(monkeypatch, plugin_dir, tmp_path):
    """The signed bytes include `sbom` — proving signing happens after it is set."""
    manifest, pub_hex = _packaged_manifest(monkeypatch, plugin_dir, tmp_path)
    assert "sbom" in manifest, "manifest should carry the sbom-source field"

    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
    sig = bytes.fromhex(manifest["signature"])

    # Flipping the sbom value must invalidate the signature (it is in scope).
    tampered = dict(manifest)
    tampered["sbom"] = "cyclonedx-py" if manifest["sbom"] != "cyclonedx-py" else "minimal-shim"
    with pytest.raises(InvalidSignature):
        pub.verify(sig, get_canonical_bytes(tampered))
