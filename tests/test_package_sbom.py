"""Tests for CycloneDX SBOM embedding in .dryadepkg bundles.

The packager must embed `sbom.cdx.json` next to `dryade.json` in every
.dryadepkg produced. If the full `cyclonedx-py` path is unavailable the
fallback minimal shim is acceptable, but the file MUST exist and MUST be
a valid CycloneDX document.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def plugin_dir(tmp_path: Path) -> Path:
    pdir = tmp_path / "sbomproof"
    pdir.mkdir()
    (pdir / "dryade.json").write_text(
        json.dumps(
            {
                "manifest_version": "2.0",
                "name": "sbomproof",
                "version": "0.1.0",
                "description": "SBOM test fixture.",
                "core_version_constraint": ">=1.0.0,<2.0.0",
                "required_tier": "starter",
                "license": "MIT",
            },
            indent=2,
        )
    )
    (pdir / "__init__.py").write_text("from .plugin import plugin\n")
    (pdir / "plugin.py").write_text(
        "class Plugin:\n"
        "    name='sbomproof'\n"
        "    version='0.1.0'\n"
        "    description='proof'\n"
        "    core_version_constraint='>=1.0.0,<2.0.0'\n"
        "    def register(self,r): pass\n"
        "plugin = Plugin()\n"
    )
    (pdir / "pyproject.toml").write_text(
        '[project]\nname = "sbomproof"\nversion = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
    )
    return pdir


def _ensure_author_key(monkeypatch, tmp_path: Path) -> None:
    """Generate an author key in an isolated $HOME so build_dryadepkg can sign."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    from dryade_plugins_sdk.cli import keys

    keys.generate_author_keypair()


def test_dryadepkg_contains_cyclonedx_sbom(monkeypatch, plugin_dir, tmp_path):
    _ensure_author_key(monkeypatch, tmp_path)

    from dryade_plugins_sdk.cli.pkg import build_dryadepkg

    pkg_path = build_dryadepkg(plugin_dir, tmp_path / "dist")
    assert pkg_path.exists()

    with tarfile.open(pkg_path, "r:gz") as tf:
        names = tf.getnames()
        assert "sbom.cdx.json" in names, f"SBOM missing from package; got {names}"
        member = tf.extractfile("sbom.cdx.json")
        assert member is not None
        sbom = json.loads(member.read().decode("utf-8"))

    assert sbom.get("bomFormat") == "CycloneDX"
    assert sbom.get("specVersion") in ("1.5", "1.6")
    # Component metadata is required by the contract.
    comp = sbom.get("metadata", {}).get("component", {})
    assert comp.get("name") == "sbomproof"
    assert comp.get("version") == "0.1.0"
    # Source is one of the two known values.
    props = sbom.get("metadata", {}).get("properties", []) or []
    sources = [p.get("value") for p in props if p.get("name") == "dryade:sbom-source"]
    assert sources, "missing dryade:sbom-source property"
    assert sources[0] in {"minimal-shim", "cyclonedx-py"}


def test_manifest_flags_sbom_source(monkeypatch, plugin_dir, tmp_path):
    _ensure_author_key(monkeypatch, tmp_path)

    from dryade_plugins_sdk.cli.pkg import build_dryadepkg

    pkg_path = build_dryadepkg(plugin_dir, tmp_path / "dist")

    with tarfile.open(pkg_path, "r:gz") as tf:
        member = tf.extractfile("dryade.json")
        assert member is not None
        manifest = json.loads(member.read().decode("utf-8"))

    # Manifest carries the SBOM source so the host can read it without
    # unpacking the SBOM file itself.
    assert manifest.get("sbom") in {"minimal-shim", "cyclonedx-py"}
