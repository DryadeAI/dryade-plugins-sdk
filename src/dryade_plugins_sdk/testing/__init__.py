"""Author-facing test fixtures.

These work in any clean Python venv — no host-runtime install required.
Plugin authors can pytest their work using only `pip install dryade-plugins-sdk`.

This subpackage has ZERO core.* imports — verified by tests/test_zero_core_imports.py.
"""

from __future__ import annotations

from dryade_plugins_sdk.testing.factories import build_agent, build_plugin, build_tool
from dryade_plugins_sdk.testing.mock_config import MockConfig
from dryade_plugins_sdk.testing.mock_host import FakeHost, FakeRegistry
from dryade_plugins_sdk.testing.mock_kv import MockKV
from dryade_plugins_sdk.testing.mock_llm import LLMCall, MockLLM

__all__ = [
    "FakeHost",
    "FakeRegistry",
    "LLMCall",
    "MockConfig",
    "MockKV",
    "MockLLM",
    "build_agent",
    "build_plugin",
    "build_tool",
]
