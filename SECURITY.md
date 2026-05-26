# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Do not file public issues for security vulnerabilities.**

Use one of these channels:

1. **GitHub Security Advisories (preferred):**
   https://github.com/DryadeAI/dryade-plugins-sdk/security/advisories/new
2. **Email:** security@dryade.ai (PGP key on request).

We aim to:

- **Acknowledge** within 72 hours of receipt.
- **Provide an initial assessment** within 5 business days.
- **Ship a fix** within 90 days for high-severity reports; sooner where
  practical.

## Scope

This policy covers the `dryade-plugins-sdk` Python package and the
`dryade-cli` author tooling. Issues in the broader Dryade platform
(runtime, marketplace, plugin manager) should be reported at
https://dryade.ai/security.

In-scope examples (non-exhaustive):

- A bug in the CLI that causes the packager to emit a `.dryadepkg`
  whose embedded hash does not match the bundled source (hash drift).
- A flaw in the SDK that lets an author bypass `--tier community`
  rejection at validate time.
- Any path in the SDK or CLI that exfiltrates the author's private signing
  key off disk.

For the canonical industry-wide definition of what constitutes a
vulnerability — and to align this policy with established practice —
see:

- **OWASP Top 10** — https://owasp.org/www-project-top-ten/
- **CWE** (Common Weakness Enumeration) — https://cwe.mitre.org/
- **Coordinated Vulnerability Disclosure (CVD) FIRST guideline** —
  https://www.first.org/global/sigs/vrdx/multiparty/guidelines

We follow the **FIRST PSIRT Services Framework v1.1** as our internal
triage standard.

## Out of scope

- Vulnerabilities in Dryade runtime, marketplace, or plugin manager —
  report at https://dryade.ai/security instead.
- Issues that require a malicious local user with shell access.
- Theoretical concerns without a working PoC.

## Hall of Fame

Reporters who follow this policy and provide a clear PoC are credited in
the all-contributors list with the `security` emoji, unless they request
anonymity.
