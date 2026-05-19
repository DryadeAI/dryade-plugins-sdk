"""F3.2: All stable contract symbols must be importable from ``dryade_plugins_sdk``."""

from __future__ import annotations


def test_all_top_level_imports() -> None:
    """Every documented symbol resolves from the package root."""
    from dryade_plugins_sdk import (  # noqa: F401
        Agent,
        AgentCapabilities,
        AgentCapability,
        AgentCard,
        AgentExecutionError,
        AgentFramework,
        AgentResult,
        CONTRACT_VERSION,
        Config,
        DryadePluginError,
        HashMismatchError,
        HealthCheck,
        IsolationLevel,
        KV,
        Leash,
        ManageableComponent,
        ManifestV2,
        ManifestValidationError,
        OutputContract,
        Plugin,
        PluginValidationError,
        Route,
        Tool,
        compute_plugin_hash_pair,
        hook,
        load_private_key,
        route,
        sign_manifest,
        tool,
        traced,
        verify_plugin_hash,
    )


def test_version_attributes() -> None:
    """``__version__`` and ``__contract_version__`` are set at the published values."""
    import dryade_plugins_sdk

    assert dryade_plugins_sdk.__version__ == "1.0.0"
    assert dryade_plugins_sdk.__contract_version__ == 4


def test_testing_submodule() -> None:
    """``dryade_plugins_sdk.testing`` exposes the eight author-facing fixtures."""
    from dryade_plugins_sdk.testing import (  # noqa: F401
        FakeHost,
        FakeRegistry,
        LLMCall,
        MockConfig,
        MockKV,
        MockLLM,
        build_agent,
        build_plugin,
        build_tool,
    )


def test_hooks_decorators() -> None:
    """``traced`` and ``hook`` are importable from the package root."""
    from dryade_plugins_sdk import hook, traced  # noqa: F401


def test_packaging_primitives_importable() -> None:
    """All four packaging primitives plus the CONTRACT_VERSION constant resolve."""
    from dryade_plugins_sdk import (
        CONTRACT_VERSION,
        compute_plugin_hash_pair,
        load_private_key,
        sign_manifest,
        verify_plugin_hash,
    )

    # Smoke: confirm they are actually callables (or a constant).
    assert callable(compute_plugin_hash_pair)
    assert callable(sign_manifest)
    assert callable(load_private_key)
    assert callable(verify_plugin_hash)
    assert isinstance(CONTRACT_VERSION, int)
