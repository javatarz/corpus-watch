# ADR-0001: Greenfield build over fork or upstream contribution to `krishnakuruvadi/portfoliomanager`

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

Before writing any code for corpus-watch, we audited the closest existing FOSS Indian net worth tracker — [`krishnakuruvadi/portfoliomanager`](https://github.com/krishnakuruvadi/portfoliomanager) (Django, GPL-3.0, family-aware, Indian asset coverage including PPF/EPF/SSY/MF/gold). The project advertises ~70% overlap with corpus-watch's MVP scope.

The user's stated principle is "avoid building if a free tool already exists." A structured audit was run to determine the right path: use as-is, fork & extend, contribute upstream, or greenfield.

Audit document: [`docs/eval/portfoliomanager-AUDIT.md`](../eval/portfoliomanager-AUDIT.md).

## Options considered

1. **Use as-is** — adopt portfoliomanager unchanged; contribute fixes when needed.
2. **Fork & extend** — fork, diverge, maintain independently.
3. **Contribute upstream** — submit MVP gaps as PRs to the existing project.
4. **Greenfield** — build corpus-watch from scratch, reusing only vetted libraries.

## Decision

**Greenfield.**

### Reasons (audit-evidenced)

1. **MVP coverage too thin.** Of ~15 hard MVP requirements (audit Section P), portfoliomanager satisfies fewer than half. NPS missing entirely (Sections D, E). EPF has no PDF import (Section E). Missed-deposit audit absent (Section J). AMFI integration and projection engine are wrong shape (Sections E, H). Closing these gaps approaches the cost of building from scratch with a far cleaner result.

2. **Architectural shape misaligned.** Hardcoded asset-class fan-out across the data model (audit Sections C, O). Adding a new asset class requires ~10 file edits and 2 migrations. Retrofitting a registry/plugin pattern is itself a rewrite. corpus-watch's principle of asset-class extensibility is incompatible with the existing structure.

3. **Privacy and quality posture diverges.** Frontend pulls 7 CDN-hosted libraries (privacy leak vs corpus-watch's no-CDN principle, Section L). Plaintext master password file at `media/secrets/passwords.json` (Section F). Selenium-only test suite pinned to a deprecated chromedriver (Section M). Each is correctable, but together they signal a different ethos. corpus-watch's "privacy is the product" stance and CI-first quality bar require a clean foundation, not progressive remediation of existing technical debt.

### Additional signals (not load-bearing, but reinforcing)

- Bus factor of 1; no human PRs in 6 months.
- Schema typos baked into column names (`*_conitrib`).
- Phone-home ping to maintainer's GitHub raw URL.
- Hidden runtime dependency on Apache Tika (JVM).

## Consequences

### Accepted costs

- Solo-dev time investment to build foundations from zero (data model, ingestion pipeline, projection engine, UI shell).
- Risk of underestimating effort. Mitigation: time-boxed cards in backlog; reuse vetted libraries instead of reimplementing parsers.
- Owning all maintenance going forward.

### Enabled gains

- Clean schema with family-aware, registry-based asset classes from day one.
- Privacy-first frontend (no CDN, no telemetry) without unwinding existing dependencies.
- Modern Python + React stack matching solo-dev preferences.
- AGPL-3.0 from day one.
- CI-first, type-checked, tested codebase from first commit.

### Foreclosed options

- Inheriting portfoliomanager's existing user base.
- Influencing portfoliomanager's direction. (We may still upstream specific patches to libraries — e.g., `casparser` — independently.)

## Reuse from audit

The audit identified specific libraries worth reusing without forking the whole codebase:

- `casparser` (MIT) — CAS PDF parsing
- `pyxirr` (Apache-2.0) — XIRR calculation
- `mftool` (MIT) — fallback MF NAV utilities
- `yfinance` (Apache-2.0) — stock EOD prices

All AGPL-3.0 compatible.

The audit also flagged a useful idempotency pattern at `portfoliomanager/src/mutualfunds/mf_helper.py:92-99` — the CAS transaction dedupe key shape. Worth referencing (not copying verbatim) when designing card #8 (CAS import).

## References

- [Audit document](../eval/portfoliomanager-AUDIT.md)
- [VISION.md](../VISION.md)
- [SCOPE.md](../SCOPE.md)
- GPL-3.0 §13 (governs combination with AGPL-3.0)
