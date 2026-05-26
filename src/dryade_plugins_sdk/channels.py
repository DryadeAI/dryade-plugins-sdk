"""Channel adapter Protocol — voice / messaging plugin contract.

This module has zero host-runtime imports — it is a pure contract.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ChannelMessage(Protocol):
    """Wire shape of a message flowing through a channel adapter."""

    content: str
    sender: str
    timestamp: float


@runtime_checkable
class Channel(Protocol):
    """A channel adapter plugin (voice, chat, email, ...).

    Attributes:
        name: stable identifier the host uses for routing.

    Methods:
        send: deliver a message outbound (e.g. send SMS).
        receive: pull the next inbound message.
    """

    name: str

    async def send(self, message: ChannelMessage) -> None: ...
    async def receive(self) -> ChannelMessage: ...
