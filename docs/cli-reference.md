# CLI Reference

The `dryade` CLI ships in the separate `dryade-cli` package. Install it with:

```bash
uv tool install dryade-cli
```

`dryade --help` lists the top-level commands. `dryade plugin --help`
lists the plugin-authoring subcommands.

## `dryade plugin keygen`

Generate an Ed25519 dev keypair for signing plugin packages.

```bash
dryade plugin keygen
```

Output:

```
~/.dryade-author/dev-key.priv  (mode 0o600)
~/.dryade-author/dev-key.pub
```

The CLI refuses to load keys with weaker permissions (D-08). Re-run keygen
to rotate; the marketplace records each public key fingerprint you submit
under, so rotated keys remain valid for previously-signed packages.

## `dryade plugin new <name>`

Scaffold a new plugin directory from the tier-specific template.

```bash
dryade plugin new my_plugin --tier starter
```

**Required argument:** `name` — snake_case, 2-50 chars, `^[a-z][a-z0-9_]{1,49}$`.

**Options:**

- `--tier {starter,team,enterprise}` — Rule §11 enforces this set.
- `--out PATH` — output directory (default: current working dir).
- `--description STRING` — overrides default placeholder.
- `--author STRING` — author field (default: empty placeholder).

The scaffolded directory is immediately validate-able and package-able.
The starter tier produces 7 files; team and enterprise overlay 3 extras on
top of the starter base.

**Exit codes:** `0` on success, `1` on schema / tier / name validation
error.

## `dryade plugin validate [path]`

Validate a plugin against the v2 schema + Plugin Protocol + hash algorithm.

```bash
dryade plugin validate                # cwd
dryade plugin validate ./my_plugin
```

Checks (in order):

1. Manifest schema (Draft 2020-12).
2. `--tier community` rejection (Rule §11).
3. `__init__.py` + `pyproject.toml` presence.
4. Plugin Protocol conformance (`isinstance(plugin, Plugin)`).
5. Custom-plugin-slot disclosure if relevant (D-10).

Exit `0` on success, `1` on first failure (each error is named in stdout).

## `dryade plugin package [path]`

Package a validated plugin into a `.dryadepkg` archive.

```bash
dryade plugin package                                  # cwd, output ./dist/
dryade plugin package ./my_plugin --output ./dist
```

**Options:**

- `--output PATH` — output directory (default: `./dist/`).
- `--no-verify` does not exist. Fail-closed (CLAUDE.md Rule §4).

Output: `<name>-<version>.dryadepkg` — a gzipped tar archive containing:

- `dryade.json` with signed hashes and Ed25519 signature.
- The plugin's `__init__.py`, `plugin.py`, and any other `.py` files.

Author key material is **never** bundled (T-339-04-03 mitigation).

## `dryade plugin doctor`

Diagnose author-tooling environment. Checks Python version, CLI version,
SDK version, author keypair shape, OpenTelemetry availability.

```bash
dryade plugin doctor
```

Exit `0` if everything is reachable, `1` otherwise (named in stdout).

## Common flags

- `-v` / `--verbose` — extra diagnostic logging.
- `--version` — print the CLI version and exit.
- `--help` / `-h` — print contextual help.

## Environment variables

The CLI honors:

- `HOME` — author keys land under `$HOME/.dryade-author/`.

It does **not** honor any `DRYADE_DISABLE_*` or `--unsafe-*` toggles —
fail-closed everywhere (Rule §4 of CLAUDE.md).
