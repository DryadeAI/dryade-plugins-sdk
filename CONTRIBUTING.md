# Contributing to dryade-plugins-sdk

Thanks for your interest in contributing.

## Quick start

    git clone https://github.com/DryadeAI/dryade-plugins-sdk
    cd dryade-plugins-sdk
    python -m venv .venv && source .venv/bin/activate
    pip install -e ".[testing]" pytest jsonschema ruff mypy
    pytest

## Branch policy (server-enforced)

`main` is **server-side branch-protected**: direct `git push origin main` is REJECTED for everyone including the owner. Force-push and deletion are blocked absolutely. **Every change funnels through a pull request** for audit trail and CI gating.

    git switch -c <your-branch-name>
    # commit your changes
    git push -u origin <your-branch-name>
    gh pr create --base main --title "..." --body "..."
    # wait for required checks to pass, then a maintainer self-merges via gh pr merge --squash

`required_approving_review_count` is 0 (solo-maintainer self-merge model); the PR exists for the CI gate and the audit trail, not for human review. If you ever see `protected branch hook declined`, switch to the PR flow above — direct pushes are blocked by design.

## Required CI checks

Your PR must pass:

- `pytest` (full suite — Python 3.11, 3.12, 3.13)
- `pytest tests/test_zero_core_imports.py` (enforcement — the SDK NEVER imports from the host runtime)
- `pytest tests/test_hash_conformance.py` (hash algorithm byte-identical to the host runtime)
- `pytest tests/test_smoke_e2e.py` (scaffold → validate → package smoke)
- `ruff check src/ tests/` (lint)
- `mypy src/dryade_plugins_sdk` (typecheck)

## Non-negotiable invariants

1. **Zero host-runtime imports.** This SDK is a pure CONTRACT package. It defines
   Protocols that the Dryade runtime implements, not the other way around. The host-imports gate test
   AST-scans every file in `src/` and fails the build on any `from core.` or `import core`.

2. **Hash algorithm parity.** `compute_plugin_hash_pair` must produce
   byte-identical SHA-256 and SHA3-256 digests as the Dryade runtime's hash function. The `test_hash_conformance.py` test
   independently reimplements the algorithm and asserts equality.

3. **Tier names.** Valid `required_tier` values: `starter`, `team`,
   `enterprise`. **Never** add `community`, `dev`, `sovereign`, or any other.
   The schema enum is locked.

4. **Fail-closed everywhere.** No `--skip-X`, no `--unsafe-Y`, no
   `DRYADE_DISABLE_*` env-vars in the SDK or CLI.

5. **Public docs only.** The SDK is the public face of Dryade plugin authoring.
   Documentation must not leak internal mechanics: pinned-pubkey paths, allowlist
   format, marketplace internals, port numbers. See
   `tests/test_no_internal_leaks.py` for the forbidden-pattern list.

## Releasing

Maintainers only. Push a tag `v<major>.<minor>.<patch>` from `main`. The
`publish.yml` workflow auto-publishes to PyPI via OIDC trusted publisher.
Tag must match `[project].version` in `pyproject.toml`.

## Reporting security issues

Do NOT open a public issue. Email `security@dryade.ai`.
