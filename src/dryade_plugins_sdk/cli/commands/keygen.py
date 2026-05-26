"""``dryade plugin keygen`` — author dev key generation.

Generates ``~/.dryade-author/dev-key.{priv,pub}`` with strict perms
(0o600 / 0o700). NEVER prints the private key — only the public hex,
so the author can register the pubkey with the marketplace.

Refuses to overwrite an existing key without ``--force`` (opt-in rotation
only, with a clear remediation message explaining that prior plugin
signatures become invalid).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from dryade_plugins_sdk.cli.keys import generate_author_keypair


def keygen(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing key (invalidates prior plugin signatures)",
        ),
    ] = False,
) -> None:
    """Generate or rotate your Dryade plugin author signing key.

    Creates ``~/.dryade-author/dev-key.priv`` (mode 0o600) and
    ``~/.dryade-author/dev-key.pub`` (hex string). The private key signs
    your ``.dryadepkg`` artifacts when you run ``dryade plugin package``.
    """
    # We only consume the public hex from the return tuple. The private bytes
    # are written to disk inside generate_author_keypair and never touched here.
    try:
        _, pub_hex = generate_author_keypair(force=force)
    except FileExistsError as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    # Resolve path display at call time — keeps test suites that
    # monkeypatch HOME per-test honest, and matches what
    # generate_author_keypair actually wrote.
    key_dir = Path.home() / ".dryade-author"
    key_priv = key_dir / "dev-key.priv"
    key_pub = key_dir / "dev-key.pub"

    if force:
        typer.secho(
            "Author key ROTATED — prior plugin signatures are now invalid.",
            fg=typer.colors.YELLOW,
            bold=True,
        )
        typer.echo("  Re-run `dryade plugin package` for every plugin you previously signed,")
        typer.echo("  then re-submit them to the marketplace.")
        typer.echo()

    typer.secho("Author keypair generated:", fg=typer.colors.GREEN)
    typer.echo(f"  Private key: {key_priv} (0600)")
    typer.echo(f"  Public key:  {key_pub}")
    typer.echo(f"  Public hex:  {pub_hex}")
    typer.echo()
    typer.secho("NEVER commit your private key.", fg=typer.colors.RED, bold=True)
    typer.echo(f"  Add `{key_dir}/` to your global .gitignore.")
    typer.echo("  Or run: echo '.dryade-author/' >> ~/.config/git/ignore")
