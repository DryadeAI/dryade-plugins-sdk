"""dryade plugin package — produce a signed .dryadepkg for marketplace submission.

Fail-closed (Rule §3, §4): a missing or unreadable author key exits non-zero
with a clear `dryade plugin keygen` remediation. The command exposes no
hash-bypass or signature-bypass option of any kind.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from dryade_plugins_sdk.cli.pkg import build_dryadepkg


def package_plugin(
    plugin_dir: Annotated[Path, typer.Argument(help="Plugin directory")] = Path("."),
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory to write the .dryadepkg into"),
    ] = Path("./dist"),
) -> None:
    """Produce a signed `.dryadepkg` ready for marketplace submission."""
    plugin_dir = plugin_dir.resolve()

    # 339-04b ships dryade_plugins_sdk.cli.keys. The 04a-only state surfaces a clear error.
    try:
        # Re-resolve the path at call time (NOT at module-import time). The
        # AUTHOR_KEY_PRIV constant is frozen at keys.py import time against
        # whatever HOME was set then; in test suites that monkeypatch HOME
        # per test the constant would point at the wrong tmp_path. Compute
        # the path fresh from the current Path.home() value.
        import dryade_plugins_sdk.cli.keys  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        typer.secho(
            "Author key infrastructure not present.\n"
            "Run `dryade plugin keygen` first (ships in plan 339-04b).",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    author_key_priv = Path.home() / ".dryade-author" / "dev-key.priv"
    if not author_key_priv.exists():
        typer.secho(
            f"No author key found at {author_key_priv}.\nRun `dryade plugin keygen` first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    try:
        pkg = build_dryadepkg(plugin_dir, output)
    except FileNotFoundError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:  # noqa: BLE001 -- surface anything else cleanly
        typer.secho(f"Packaging failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Packaged: {pkg}", fg=typer.colors.GREEN)
    typer.echo()
    typer.echo("Submit to the marketplace at: https://marketplace.dryade.ai/submit")
