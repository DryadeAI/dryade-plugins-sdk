"""SDK exception hierarchy.

PURE CONTRACT: defined here so plugins never need to `from core.exceptions import ...`.
Core's own exception hierarchy continues to live in core.exceptions; the SDK's
hierarchy is parallel — names match but the classes are distinct.
"""

from __future__ import annotations


class DryadePluginError(Exception):
    """Base for all SDK-raised errors."""


class PluginValidationError(DryadePluginError):
    """Manifest or contract validation failed."""


class ManifestValidationError(PluginValidationError):
    """Specific to manifest schema mismatches."""


class AgentExecutionError(DryadePluginError):
    """Agent runtime failure (matches core's AgentExecutionError shape)."""


class HashMismatchError(DryadePluginError):
    """SHA-256 or SHA3-256 hash drifted from the recorded digest."""
