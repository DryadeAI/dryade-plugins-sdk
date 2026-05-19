"""``dryade plugin doctor`` — author-side diagnostic (D-12).

Walks a plugin directory and reports common authoring mistakes BEFORE the
plugin gets submitted to the marketplace:

- Missing ``dryade.json`` / unparseable JSON.
- ``manifest_version`` != ``"2.0"`` (Phase 339-02 closed v1 schema).
- ``required_tier`` == ``"community"`` (Rule §11 violation).
- ``plugin_hash_sha256`` baked into the manifest no longer matches what
  ``compute_plugin_hash_pair`` produces on the current source tree —
  Rule §9 freshness gate: editing a ``.py`` invalidates the prior package
  signature. Doctor catches this BEFORE allowlist push so the author
  doesn't ship a stale .dryadepkg.
- Missing ``pyproject.toml`` (required by ``lint_plugins.py``).

Doctor is the author-side counterpart to F4.8 — lint never verifies
signatures or hash freshness. Doctor runs locally; end-user doctor for
allowlist-rejection diagnosis is deferred to Phase 341.

NO ``--skip-hash-check``, ``--quiet``, or ``--allow-stale`` flags exist.
Every issue surfaces with an explicit, actionable remediation pointer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from dryade_plugins_sdk.packaging import compute_plugin_hash_pair


def doctor(
    plugin_dir: Annotated[
        Path,
        typer.Argument(help="Plugin directory to diagnose"),
    ] = Path("."),
) -> None:
    """Diagnose common plugin issues (manifest drift, stale hash, missing files).

    Exits 0 with a green check on a clean plugin, exits 1 with a numbered
    list of issues on any drift. Use this between ``dryade plugin package``
    invocations to catch hash staleness BEFORE submission.
    """
    plugin_dir = plugin_dir.resolve()
    issues: list[str] = []

    typer.secho(f"Checking plugin: {plugin_dir}", fg=typer.colors.CYAN)

    # 1. Manifest exists + parses.
    manifest_path = plugin_dir / "dryade.json"
    manifest: dict = {}
    if not manifest_path.exists():
        issues.append("Missing dryade.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            issues.append(f"Manifest invalid JSON: {e}")
            manifest = {}

        # 2. Stale hash detection (Rule §9 freshness).
        embedded_sha256 = manifest.get("plugin_hash_sha256")
        if embedded_sha256:
            try:
                actual_sha256, _ = compute_plugin_hash_pair(plugin_dir)
            except Exception as e:  # noqa: BLE001 -- never crash doctor on hash failure
                issues.append(f"Could not recompute plugin hash: {e}")
            else:
                if embedded_sha256 != actual_sha256:
                    issues.append(
                        f"Stale plugin_hash_sha256 — manifest says "
                        f"{embedded_sha256[:16]}..., actual is "
                        f"{actual_sha256[:16]}... (hash mismatch). "
                        "Re-run `dryade plugin package` to refresh the signed bundle."
                    )

        # 3. Manifest version check (must be v2 after Phase 339-02).
        manifest_version = manifest.get("manifest_version")
        if manifest_version and manifest_version != "2.0":
            issues.append(
                f"Manifest version is {manifest_version!r}, expected '2.0'. "
                "Run `dryade plugin validate` for the full schema diff."
            )

        # 4. Required tier check (Rule §11 — community is not a valid tier).
        required_tier = manifest.get("required_tier")
        if required_tier == "community":
            issues.append(
                "Rule §11 violation: required_tier='community' is not allowed. "
                "Valid tiers: starter, team, enterprise."
            )

    # 5. pyproject.toml presence (required by tools/lint_plugins.py).
    if not (plugin_dir / "pyproject.toml").exists():
        issues.append("Missing pyproject.toml")

    if issues:
        typer.secho(f"\n{len(issues)} issue(s) found:", fg=typer.colors.RED, bold=True)
        for i, msg in enumerate(issues, 1):
            typer.echo(f"  {i}. {msg}")
        raise typer.Exit(code=1)

    typer.secho("OK — no issues detected", fg=typer.colors.GREEN)
