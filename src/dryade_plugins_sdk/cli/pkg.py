"""`.dryadepkg` builder — produces a marketplace submission artifact.

Format: gzipped tar containing the plugin's source tree plus a re-signed
dryade.json carrying both plugin_hash_sha256 + plugin_hash_sha3_256 (the
dual-hash contract, v4) and a 128-char hex Ed25519 signature from the author's
~/.dryade-author/dev-key.priv key.

``dryade_plugins_sdk.cli.keys`` exports ``load_author_private_key`` and the
canonical key path. This module imports the key loader LAZILY so a missing
install surfaces a clear "Run keygen first" error rather than a Python
ImportError stacktrace.

Security invariants:
  - EXCLUDED_PATTERNS contains ``.dryade-author`` so the author's private key
    is NEVER bundled, even if the author left a stray copy in the plugin dir.
  - Signature is computed over the same canonical bytes the workbench JS
    verifier reads, so cross-runtime verification stays parity-clean.
"""

from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from dryade_plugins_sdk.packaging import (
    CONTRACT_VERSION,
    compute_plugin_hash_pair,
    sign_manifest,
)

INCLUDED_FILES = {
    "dryade.json",
    "__init__.py",
    "plugin.py",
    "pyproject.toml",
    "README.md",
    "LICENSE",
    ".gitignore",
}
INCLUDED_DIRS = {"tests", "src", "ui"}
EXCLUDED_PATH_FRAGMENTS = {
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    ".venv",
    "venv",
    "dist",
    "build",
    ".egg-info",
    ".dryade-author",  # NEVER bundle author key
}


def _should_include(rel_path: Path) -> bool:
    """Decide whether a path inside the plugin dir lands in the bundle."""
    parts = rel_path.parts
    # Strip dotfiles except for the canonical .gitignore.
    for p in parts:
        if p.startswith(".") and p != ".gitignore":
            # Explicit dotfile exclusions cover anything under
            # .dryade-author/, .venv/, .pytest_cache/ etc.
            return False
    # Reject any path that walks through an excluded directory.
    for frag in EXCLUDED_PATH_FRAGMENTS:
        if any(frag in p for p in parts):
            return False
    if parts[0] in INCLUDED_DIRS:
        return True
    if str(rel_path) in INCLUDED_FILES:
        return True
    return False


def build_dryadepkg(plugin_dir: Path, output_dir: Path) -> Path:
    """Build a signed `.dryadepkg` from a plugin directory.

    Args:
        plugin_dir: Path to the plugin source directory.
        output_dir: Where to write ``<name>-<version>.dryadepkg``.

    Returns:
        Path to the produced ``.dryadepkg``.

    Raises:
        FileNotFoundError: if the plugin's ``dryade.json`` is missing or the
            author key has not been generated (delegated via the lazy import).
    """
    # Lazy import so 04a-only state surfaces a clear error rather than
    # a missing-module stacktrace.
    from dryade_plugins_sdk.cli.keys import load_author_private_key

    manifest_path = plugin_dir / "dryade.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No dryade.json at {manifest_path}")
    manifest: dict[str, Any] = json.loads(manifest_path.read_text())

    # Strip any prior signatures — we re-sign every package.
    manifest.pop("signature", None)
    manifest.pop("signature_pq", None)

    sha256_hex, sha3_256_hex = compute_plugin_hash_pair(plugin_dir)
    manifest["plugin_hash_sha256"] = sha256_hex
    manifest["plugin_hash_sha3_256"] = sha3_256_hex
    manifest["contract_version"] = CONTRACT_VERSION

    name = manifest["name"]
    version = manifest["version"]
    output_dir.mkdir(parents=True, exist_ok=True)
    pkg_path = output_dir / f"{name}-{version}.dryadepkg"

    # Build the CycloneDX SBOM for the plugin. Full path uses cyclonedx-py;
    # fallback is a minimal shim flagged via metadata.properties so consumers
    # can distinguish the two at audit time.
    from dryade_plugins_sdk.cli.sbom import build_sbom

    sbom_doc = build_sbom(plugin_dir, name, version)
    sbom_source = "minimal-shim"
    for prop in sbom_doc.get("metadata", {}).get("properties", []) or []:
        if prop.get("name") == "dryade:sbom-source":
            sbom_source = prop.get("value") or sbom_source
            break
    # Flag the SBOM source on the manifest itself so the host (and
    # downstream provenance checks) can read it from dryade.json without
    # unpacking sbom.cdx.json.
    manifest["sbom"] = sbom_source

    # Sign LAST — after every content field (hashes, contract_version, sbom)
    # is in place — so the Ed25519 signature covers the final manifest. Signing
    # before adding `sbom` would leave that field outside the signed canonical
    # bytes, and the signature would fail to verify on the produced package.
    priv = load_author_private_key()
    manifest["signature"] = sign_manifest(manifest, priv)

    # Write the re-signed manifest to a temp file so we can tar-add it under
    # the canonical arcname while leaving the on-disk dryade.json untouched.
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        tmp.write(json.dumps(manifest, sort_keys=True, indent=2))
        tmp_manifest_path = Path(tmp.name)

    # Write the SBOM to a sibling temp file we can add under the canonical
    # arcname `sbom.cdx.json` without leaving it in the plugin tree.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".cdx.json", delete=False, encoding="utf-8"
    ) as tmp_sbom:
        tmp_sbom.write(json.dumps(sbom_doc, sort_keys=True, indent=2))
        tmp_sbom_path = Path(tmp_sbom.name)

    try:
        with tarfile.open(pkg_path, "w:gz") as tf:
            tf.add(tmp_manifest_path, arcname="dryade.json")
            tf.add(tmp_sbom_path, arcname="sbom.cdx.json")
            for f in sorted(plugin_dir.rglob("*")):
                if not f.is_file():
                    continue
                rel = f.relative_to(plugin_dir)
                if rel.name == "dryade.json":
                    # The signed copy was already added under arcname=dryade.json.
                    continue
                if rel.name == "sbom.cdx.json":
                    # Skip any pre-existing SBOM; we just added our freshly
                    # generated one under the canonical arcname.
                    continue
                if _should_include(rel):
                    tf.add(f, arcname=str(rel))
    finally:
        tmp_manifest_path.unlink(missing_ok=True)
        tmp_sbom_path.unlink(missing_ok=True)

    return pkg_path
