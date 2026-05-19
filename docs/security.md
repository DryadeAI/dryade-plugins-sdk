# Security for plugin authors

What every plugin author must know about hashing, signing, tier slots,
and how the host enforces them. **This page is not a security policy** —
that lives at [SECURITY.md](https://github.com/DryadeAI/dryade-plugins-sdk/blob/main/SECURITY.md)
and covers vulnerability reporting.

## Author signing keys

`dryade plugin keygen` generates your Ed25519 dev keypair:

- `~/.dryade-author/dev-key.priv` — mode `0o600`, fail-closed at load.
- `~/.dryade-author/dev-key.pub` — embedded into the `.dryadepkg`.

The CLI refuses to load keys with weaker permissions (D-08). Rotate by
re-running keygen; the marketplace tracks public-key fingerprints, so
old signatures remain valid for already-submitted packages.

**Never check author keys into source control.** The `.gitignore` shipped
by the scaffolder excludes `~/.dryade-author/` already; if you create
custom paths, ignore those too.

## Hash conformance (Rule §9)

Every plugin source file (every `.py` under your plugin directory, excluding
`__pycache__/`) gets dual-hashed:

- SHA-256 digest of each file's `path:contents` pair, then chained.
- SHA3-256 digest of the same, in parallel.

The final 64-char hex digests land in the packaged manifest's
`plugin_hash_sha256` and `plugin_hash_sha3_256` fields, plus a
`contract_version: 4` marker.

The host re-computes both at load time and refuses any plugin whose
on-disk source drifts from the manifest-embedded hash. Authors who
modify code after packaging must re-run `dryade plugin package` to
produce a fresh signed archive.

## Tier slots (Rule §11)

`required_tier` must be `starter`, `team`, or `enterprise`. **Never
`community`.** The CLI rejects `community` at scaffold + validate +
package time, and the host's allowlist gate refuses to load a
`community`-tiered plugin even if you bypass the CLI.

| Tier | Typical install profile |
|------|-------------------------|
| `starter` | 1-user installs, hobbyist / solo dev |
| `team` | up to N users (set in the customer's signed allowlist) |
| `enterprise` | multi-org installs with full slot allocation |

Tier limits are decided by the customer's PM-signed allowlist, not by
the SDK or CLI. Your plugin's `required_tier` is the **floor** — the
customer's tier must be ≥ this value.

## Why you cannot leak the customer's allowlist

The plugin runs after the host has already loaded the allowlist and
verified your signature. From inside a plugin you cannot:

- Read the customer's `~/.dryade/allowed-plugins.json`.
- Read the PM's TOFU-pinned signing key.
- Force a re-signing pass.

Your Leash sandbox + the Plugin Tool Bridge enforce these boundaries.
If you discover a path that breaks them, see
[SECURITY.md](https://github.com/DryadeAI/dryade-plugins-sdk/blob/main/SECURITY.md)
— it is a CVE-class vulnerability.

## What's *not* the SDK's problem

The SDK does not implement:

- License signing / heartbeat / device caps — these live in PM
  (`dryade-pm`).
- Allowlist verification — core does this at plugin load time.
- Marketplace re-signing — marketplace does this when you submit.

You only interact with the **author** half of the security model — your
signing keys, your hashes. Everything downstream is the host's problem.

## Cross-references

- [SECURITY.md](https://github.com/DryadeAI/dryade-plugins-sdk/blob/main/SECURITY.md)
  — vulnerability reporting flow.
- [Concepts § Signing](concepts.md#signing) — high-level model.
- [Concepts § Hashing — contract version 4](concepts.md#hashing--contract-version-4)
  — the algorithm.
- [CLI Reference § keygen](cli-reference.md#dryade-plugin-keygen) — key
  generation.
