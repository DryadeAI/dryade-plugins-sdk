"""SDK ManifestV2 dataclass must accept a v2 manifest dict (consumes the v2 schema)."""

from __future__ import annotations

import pytest

from dryade_plugins_sdk.exceptions import ManifestValidationError
from dryade_plugins_sdk.manifest import ManifestV2


def test_minimal_v2_manifest_accepted() -> None:
    """A spec-minimal manifest validates and round-trips its declared fields."""
    m = ManifestV2(
        manifest_version="2.0",
        name="example",
        version="1.0.0",
        description="example plugin",
        required_tier="starter",
        author="me",
        core_version_constraint=">=1.0.0",
    )
    assert m.name == "example"
    assert m.manifest_version == "2.0"
    assert m.required_tier == "starter"


def test_v1_manifest_rejected() -> None:
    """v1 manifests must raise ``ManifestValidationError`` (hard cutover)."""
    with pytest.raises(ManifestValidationError):
        ManifestV2(
            manifest_version="1.0",  # v1 — must reject
            name="example",
            version="1.0.0",
            description="x",
            required_tier="starter",
            author="me",
            core_version_constraint=">=1.0.0",
        )


def test_community_tier_rejected() -> None:
    """``required_tier`` never accepts 'community'."""
    with pytest.raises(ManifestValidationError):
        ManifestV2(
            manifest_version="2.0",
            name="example",
            version="1.0.0",
            description="x",
            required_tier="community",  # not a valid plugin tier
            author="me",
            core_version_constraint=">=1.0.0",
        )


@pytest.mark.parametrize("tier", ["starter", "team", "enterprise"])
def test_starter_team_enterprise_accepted(tier: str) -> None:
    """Positive cases — every documented tier name validates."""
    m = ManifestV2(
        manifest_version="2.0",
        name="tier_probe",
        version="1.0.0",
        description="x",
        required_tier=tier,
        author="me",
        core_version_constraint=">=1.0.0",
    )
    assert m.required_tier == tier
