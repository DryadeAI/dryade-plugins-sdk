"""Leash Protocol — sandbox / isolation policy a plugin can request.

LIVE isolation levels: NONE, PROCESS, LANGUAGE.
STUB (fail-closed): CONTAINER, GVISOR — the host refuses at load time if the
plugin requests an isolation level the host cannot honor.

This module has zero host-runtime imports — it is a pure contract.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable


class IsolationLevel(str, Enum):
    """Sandbox isolation levels a plugin may request via its Leash.

    LIVE today:
        NONE      — no isolation (host trust level)
        PROCESS   — subprocess + resource limits (cpu/mem/network)
        LANGUAGE  — bwrap / firejail user-namespace sandbox

    STUB (fail-closed) — declared so plugins can request them in manifests, but
    the host refuses to load the plugin until the corresponding sandbox lands:
        CONTAINER — Docker / Podman process sandbox
        GVISOR    — gVisor kernel sandbox
    """

    NONE = "none"
    PROCESS = "process"
    LANGUAGE = "language"  # user-namespace sandbox
    CONTAINER = "container"  # STUB — fail-closed if requested
    GVISOR = "gvisor"  # STUB — fail-closed if requested


@runtime_checkable
class Leash(Protocol):
    """Sandbox policy a plugin can declare.

    Attributes:
        isolation: which isolation tier the plugin needs.
        cpu_quota: optional CPU quota as fraction of one core (0.0-1.0).
        memory_mb: optional resident memory cap in megabytes.
        network: True iff the plugin needs outbound network from inside the sandbox.
    """

    isolation: IsolationLevel
    cpu_quota: float | None
    memory_mb: int | None
    network: bool
