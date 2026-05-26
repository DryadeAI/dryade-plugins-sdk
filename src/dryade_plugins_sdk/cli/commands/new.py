"""dryade plugin new — scaffold a new Dryade plugin from jinja2 templates.

Guarantees:
- every emitted dryade.json validates against the v2 schema.
- every emitted tests/test_plugin.py ships meaningful assertions.
- emitted manifest carries no entry_point (callers register via plugin.register).
- emitted plugin.py imports only from dryade_plugins_sdk.
- scaffold output discloses custom_plugin_slots consumption.
- scaffold output cross-links to the security-for-authors page.
- --tier values are constrained to {starter, team, enterprise}.

Tier rendering: starter ships the full 7-file base. Team and enterprise
layer 3 overlay files (dryade.json, plugin.py, tests/test_plugin.py) on
top of the starter base so all three tiers produce a complete scaffold.
"""

from __future__ import annotations

import re
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Annotated, Any

import typer
from jinja2 import Environment, FileSystemLoader

from dryade_plugins_sdk.cli._tier import validate_tier

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,49}$")


def _derive_class_name(plugin_name: str) -> str:
    """Snake_case → PascalCase. ``my_plugin`` → ``MyPlugin``."""
    return "".join(part.capitalize() for part in plugin_name.split("_"))


def _render_tier(
    target: Path,
    tier: str,
    ctx: dict[str, Any],
    template_root: Path,
) -> None:
    """Render the starter base, then overlay the tier-specific delta files."""
    base_dir = template_root / "starter"
    env_base = Environment(
        loader=FileSystemLoader(str(base_dir)),
        keep_trailing_newline=True,
        autoescape=False,
    )
    for tpl_path in sorted(base_dir.rglob("*.j2")):
        rel = tpl_path.relative_to(base_dir)
        out_rel = Path(str(rel).removesuffix(".j2"))
        out_file = target / out_rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        rendered = env_base.get_template(str(rel)).render(**ctx)
        out_file.write_text(rendered)

    if tier == "starter":
        return

    overlay_dir = template_root / tier
    if not overlay_dir.exists():
        # Pure-starter scaffold for unknown tiers — but validate_tier already
        # rejected anything outside {starter, team, enterprise}, so this is
        # defensive only.
        return

    env_overlay = Environment(
        loader=FileSystemLoader(str(overlay_dir)),
        keep_trailing_newline=True,
        autoescape=False,
    )
    for tpl_path in sorted(overlay_dir.rglob("*.j2")):
        rel = tpl_path.relative_to(overlay_dir)
        out_rel = Path(str(rel).removesuffix(".j2"))
        out_file = target / out_rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        rendered = env_overlay.get_template(str(rel)).render(**ctx)
        out_file.write_text(rendered)


def new_plugin(
    name: Annotated[str, typer.Argument(help="Plugin name (snake_case)")],
    tier: Annotated[
        str,
        typer.Option(
            "--tier",
            "-t",
            callback=validate_tier,
            help="Target tier: starter, team, or enterprise",
        ),
    ] = "starter",
    description: Annotated[str, typer.Option("--description", "-d")] = "Example Dryade plugin",
    author: Annotated[str, typer.Option("--author", "-a")] = "Unknown",
    author_email: Annotated[str, typer.Option("--email")] = "",
    has_ui: Annotated[bool, typer.Option("--with-ui")] = False,
    out: Annotated[
        Path, typer.Option("--out", "-o", help="Parent directory for the new plugin")
    ] = Path("."),
) -> None:
    """Scaffold a new Dryade plugin from the canonical template."""
    if not _NAME_RE.match(name):
        typer.secho(
            f"Plugin name must be snake_case, 2-50 chars, lowercase alphanumeric "
            f"plus underscore. Got: {name!r}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    target = out / name
    if target.exists():
        typer.secho(
            f"Target directory already exists: {target}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # Auto-keygen if available and no author key (friction-free first run).
    # keys.py + generate_author_keypair are soft-imported so the scaffold still
    # works cleanly when they are not installed.
    try:
        from dryade_plugins_sdk.cli.keys import (
            AUTHOR_KEY_PRIV,
            generate_author_keypair,
        )

        if not AUTHOR_KEY_PRIV.exists():
            typer.secho(
                "First-run: generating author keypair at ~/.dryade-author/...",
                fg=typer.colors.CYAN,
            )
            try:
                generate_author_keypair(force=False)
            except FileExistsError:
                # The module-level path constant is resolved at import time and
                # can be stale if HOME moved; the key already exists, so there
                # is nothing to generate.
                pass
            else:
                typer.secho(
                    "  Done. NEVER commit ~/.dryade-author/dev-key.priv.",
                    fg=typer.colors.YELLOW,
                )
    except ImportError:
        # When keys.py is unavailable, defer to explicit `dryade plugin keygen`.
        pass

    template_root = Path(str(resources.files("dryade_plugins_sdk.cli") / "templates"))
    if not (template_root / tier).exists():
        typer.secho(f"Template tier not found: {tier}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    ctx: dict[str, Any] = {
        "name": name,
        "class_name": _derive_class_name(name),
        "description": description,
        "author": author,
        "author_email": author_email,
        "tier": tier,
        "has_ui": has_ui,
        "core_version_constraint": ">=1.0.0,<2.0.0",
        "year": datetime.now().year,
    }

    target.mkdir(parents=True)
    _render_tier(target, tier, ctx, template_root)

    # "Next steps" — author-facing workflow. Mentions validate + package + submit.
    typer.secho(
        f"\nScaffolded {tier}-tier plugin at {target}",
        fg=typer.colors.GREEN,
    )
    typer.echo("\nNext steps:")
    typer.echo(f"  cd {target}")
    typer.echo("  python -m venv .venv && source .venv/bin/activate")
    typer.echo("  pip install -e \".[dev]\"")
    typer.echo("  pytest")
    typer.echo("  dryade plugin validate .")
    typer.echo("  dryade plugin package .")
    typer.echo("  # then submit the .dryadepkg to the marketplace")

    # Slot disclosure across reinforcing surfaces (CLI help, this scaffold
    # output, and the security-for-authors docs). Spell out the slot ranges so
    # authors don't have to click through to learn the marketplace's slot economy.
    typer.echo()
    typer.secho("Tier and slots:", bold=True)
    typer.echo(f"  Your plugin's required_tier is '{tier}' — that controls which end-user")
    typer.echo("  license tiers can install your plugin (broader tier = wider reach):")
    typer.echo("    starter      → installable by Starter / Team / Enterprise (broadest)")
    typer.echo("    team         → installable by Team / Enterprise")
    typer.echo("    enterprise   → installable by Enterprise only (narrowest, highest ACV)")
    typer.echo("  End-user plugin slot ceilings (5 / 15 / 25 plugins per tier) are published")
    typer.echo("  at https://dryade.ai/pricing — design for high per-slot value regardless")
    typer.echo("  of which tier-license your customer holds.")
    typer.echo("  Tier reference:         https://dryade.ai/docs/sdk/concepts")

    # Cross-link to the security-for-authors page.
    typer.echo()
    typer.secho("Security model:", bold=True)
    typer.echo(
        "  Your plugin is signed with ~/.dryade-author/dev-key.priv on `dryade plugin package`."
    )
    typer.echo("  Author obligations:     https://docs.dryade.ai/plugins/security-for-authors")

    # Tier disclosure — third surface (after CLI --help and the validate_tier
    # callback). Reinforces that community is not a valid required_tier.
    typer.echo()
    typer.secho(
        "'community' is NOT a valid required_tier.",
        fg=typer.colors.YELLOW,
    )
    typer.echo("  Community Edition users have no Plugin Manager and no plugin loading.")
