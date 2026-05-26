"""CycloneDX SBOM generation for ``.dryadepkg`` bundles.

The packager calls :func:`build_sbom` to produce a CycloneDX 1.5 JSON
document describing the plugin and its declared dependencies. The SBOM
is embedded in the ``.dryadepkg`` tarball as ``sbom.cdx.json`` next to
``dryade.json``.

Two production paths:

  1. **Full SBOM**: ``cyclonedx-py`` shells out from the active venv and
     produces a complete CycloneDX 1.5 document from the plugin's
     ``pyproject.toml`` + installed deps. Falls back to (2) on any
     non-zero exit.
  2. **Minimal shim**: a hand-built skeleton with just the component
     metadata. The shim is flagged in the SBOM's ``metadata.properties``
     so consumers can tell a shim from a full SBOM.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _minimal_shim(name: str, version: str) -> dict[str, Any]:
    """Return a CycloneDX 1.5-shaped doc with only the component metadata."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "library",
                "name": name,
                "version": version,
                "bom-ref": f"{name}@{version}",
            },
            "properties": [
                {"name": "dryade:sbom-source", "value": "minimal-shim"},
            ],
        },
        "components": [],
    }


def _run_cyclonedx(pyproject_path: Path, output_path: Path) -> bool:
    """Run cyclonedx-py against a plugin's pyproject.toml.

    Returns True on success (output file populated with a valid SBOM),
    False on any failure (caller should fall back to the minimal shim).
    """
    cli = shutil.which("cyclonedx-py")
    if cli is None:
        return False
    # cyclonedx-py 4+ has subcommands: poetry / requirements / environment.
    # Reading from stdin would need a requirements file; the cleanest path is
    # `environment` against the active venv.
    cmd = [cli, "environment", "-o", str(output_path), "--output-format", "JSON"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=pyproject_path.parent,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    if proc.returncode != 0:
        return False
    if not output_path.exists() or output_path.stat().st_size == 0:
        return False
    # Sanity-check structure.
    try:
        doc = json.loads(output_path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    if doc.get("bomFormat") != "CycloneDX":
        return False
    return True


def build_sbom(plugin_dir: Path, name: str, version: str) -> dict[str, Any]:
    """Produce a CycloneDX SBOM dict for the plugin at ``plugin_dir``.

    Tries the full ``cyclonedx-py`` path first; falls back to a minimal
    shim with a ``dryade:sbom-source = minimal-shim`` property so
    consumers can distinguish full vs shim at audit time.

    Returns a dict ready to ``json.dumps``.
    """
    pyproject = plugin_dir / "pyproject.toml"
    if pyproject.exists():
        with tempfile.NamedTemporaryFile(
            "w", suffix=".cdx.json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp_path = Path(tmp.name)
        try:
            if _run_cyclonedx(pyproject, tmp_path):
                try:
                    doc = json.loads(tmp_path.read_text())
                except (OSError, json.JSONDecodeError):
                    doc = None
                if isinstance(doc, dict) and doc.get("bomFormat") == "CycloneDX":
                    # Tag the doc so consumers can tell the source apart.
                    meta = doc.setdefault("metadata", {})
                    props = meta.setdefault("properties", [])
                    if not any(
                        p.get("name") == "dryade:sbom-source" for p in props
                    ):
                        props.append(
                            {"name": "dryade:sbom-source", "value": "cyclonedx-py"}
                        )
                    return doc
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    # Fallback path: minimal shim.
    return _minimal_shim(name, version)
