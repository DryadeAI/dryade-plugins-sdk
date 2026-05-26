"""ManifestV2 — typed wrapper over the v2 JSON schema.

Validates a dict against the schema and raises ManifestValidationError on mismatch.
The v2 JSON schema is bundled into the SDK at src/dryade_plugins_sdk/_schemas/.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any, ClassVar, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from dryade_plugins_sdk.exceptions import ManifestValidationError


def _load_v2_schema() -> dict[str, Any]:
    """Locate the v2 schema file.

    Search order:
    1. Bundled in SDK package data at ``_schemas/dryade-manifest-v2.schema.json``
       (preferred path for PyPI installs).
    2. Fall back to a ``dryade-plugins/schemas/`` checkout next to the source
       tree (dev install only).

    Raises:
        FileNotFoundError: if neither location resolves.
    """
    # Path 1: bundled package data
    try:
        schema_path = (
            resources.files("dryade_plugins_sdk") / "_schemas" / "dryade-manifest-v2.schema.json"
        )
        if schema_path.is_file():
            return cast("dict[str, Any]", json.loads(schema_path.read_text()))
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass

    # Path 2: dev install fallback — walk up from this file to monorepo root
    here = Path(__file__).resolve()
    for ancestor in [here.parent] + list(here.parents):
        candidate = ancestor / "dryade-plugins" / "schemas" / "dryade-manifest-v2.schema.json"
        if candidate.exists():
            return cast("dict[str, Any]", json.loads(candidate.read_text()))

    raise FileNotFoundError(
        "dryade-manifest-v2.schema.json not found — install from PyPI or check monorepo path"
    )


@dataclass
class ManifestV2:
    """Typed wrapper over a v2 plugin manifest.

    Construction validates against the v2 schema (Draft 2020-12). Validation
    failures raise :class:`ManifestValidationError` with a concise multi-error
    summary. Fails closed — there is no env-var bypass.

    Notes:
        - ``manifest_version`` MUST be "2.0" (the schema enum locks this).
          v1 manifests raise ManifestValidationError.
        - ``required_tier`` MUST be one of ``starter`` / ``team`` / ``enterprise``.
          ``community`` is not a valid plugin tier and raises ManifestValidationError.
    """

    manifest_version: str
    name: str
    version: str
    description: str
    required_tier: str
    author: str
    core_version_constraint: str
    has_ui: bool = False
    agents: list[dict[str, Any]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    routes: list[dict[str, Any]] = field(default_factory=list)
    permissions: list[str] | dict[str, Any] = field(default_factory=list)
    api_paths: list[str] = field(default_factory=list)
    plugin_dependencies: list[str] | dict[str, Any] = field(default_factory=list)
    signature: str | None = None
    signature_pq: str | None = None
    icon: str | None = None
    ui: dict[str, Any] | None = None
    ui_bundle_hash: str | None = None
    ui_chunks_hash: str | None = None
    settings_schema: dict[str, Any] | None = None
    category: str | None = None
    display_name: str | None = None
    tags: list[str] = field(default_factory=list)
    mcp_server: dict[str, Any] | None = None
    agent_metadata: dict[str, Any] | None = None
    deprecated: bool = False
    sandbox_policy: str | None = None

    _validator: ClassVar[Draft202012Validator | None] = None

    def __post_init__(self) -> None:
        """Validate against v2 schema. Fails closed."""
        if ManifestV2._validator is None:
            ManifestV2._validator = Draft202012Validator(_load_v2_schema())

        # Convert dataclass to dict, skipping None values (not part of schema's required set).
        as_dict = {k: v for k, v in self.__dict__.items() if v is not None}

        errors = sorted(
            ManifestV2._validator.iter_errors(as_dict),
            key=lambda e: list(e.path),
        )
        if errors:
            msg = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5])
            raise ManifestValidationError(msg)
