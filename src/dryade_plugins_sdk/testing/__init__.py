"""Author-facing test fixtures.

D-07: these work in any clean Python venv — no Dryade core install required.
Plugin authors can pytest their work using only `pip install dryade-plugins-sdk`.

This subpackage has ZERO core.* imports — verified by tests/test_zero_core_imports.py.
"""

from __future__ import annotations

from dryade_plugins_sdk.testing.mock_host import FakeHost, FakeRegistry
from dryade_plugins_sdk.testing.mock_kv import MockKV
from dryade_plugins_sdk.testing.mock_config import MockConfig
from dryade_plugins_sdk.testing.mock_llm import MockLLM, LLMCall
from dryade_plugins_sdk.testing.factories import build_plugin, build_agent, build_tool

__all__ = [
    "FakeHost",
    "FakeRegistry",
    "MockKV",
    "MockConfig",
    "MockLLM",
    "LLMCall",
    "build_plugin",
    "build_agent",
    "build_tool",
]
