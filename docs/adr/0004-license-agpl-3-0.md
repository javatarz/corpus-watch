# ADR-0004: License family — AGPL-3.0

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch needs a licence. The user's stated requirements:

- Open use and modification by anyone.
- Commercial use is acceptable.
- Attribution must be retained ("I want credit").
- Visibility into commercial forks ("I want to know if someone is forking what I did and making money off of it").

These requirements are partly in tension with the strict OSI definition of open source, which forbids "no commercial use" clauses in OSI-approved licences.

## Options considered

1. **MIT** — permissive, attribution required, allows commercial use. Forks may stay private; no source-disclosure obligation. Maximum freedom for downstream, minimum visibility for upstream.
2. **Apache-2.0** — like MIT, plus an explicit patent grant. Same visibility limitation.
3. **AGPL-3.0** — strong copyleft. Allows commercial use. Distinguishing clause: §13 requires source disclosure to *network users* of derivative works. Hosting a modified version on a public server triggers source-disclosure obligation. This is the mechanism by which commercial forks become visible.
4. **GPL-3.0** — strong copyleft, but only triggers on distribution, not network use. A commercial SaaS could host a fork without publishing source. Insufficient visibility for our threat model.
5. **PolyForm Noncommercial 1.0** — source-available, explicitly bans commercial use. Loses OSI-approved status; smaller contributor pool; legally inconsistent with the user's "commercial OK" stance.
6. **Source-available with custom non-compete (BUSL, FSL)** — commercial-hostile, time-bombed open. Custom restrictions; ecosystem friction.

## Decision

**AGPL-3.0** (with `-or-later` clause per [ADR-0003](0003-license-clause-or-later.md)).

### Reasons

- **Allows commercial use.** Aligns with the user's "commercial OK" stance.
- **Visibility into hosted forks.** AGPL §13 forces any networked deployment of a derivative to publish source. A commercial entity wanting to monetise a fork must either publish their changes (giving us visibility and allowing reciprocal benefit) or stop hosting. This is exactly the "I want to know if they fork it" outcome.
- **Attribution baked in.** Copyright notices and license text travel with the code.
- **Patent grant.** AGPL-3.0 inherits GPL-3.0's patent termination clause (cleaner than MIT).
- **Ecosystem alignment.** Peer privacy / self-hosted projects (Ghostfolio, Sure, Mastodon, etc.) use AGPL-3.0. Reduces friction.
- **OSI-approved.** Preserves "true open source" badge, contribution-friendly.

## Consequences

### Accepted

- Some commercial actors avoid AGPL because of the source-disclosure obligation. We accept that as a feature, not a bug — it filters in the kind of commercial use we want visibility into.
- Cannot combine corpus-watch source with code under AGPL-incompatible licences (most proprietary, some restrictive open licences). Acceptable: our dependencies are MIT/Apache/BSD/PSF (audit-confirmed via [ADR-0001](0001-greenfield-over-portfoliomanager.md) Section A).

### Enabled

- Public forks remain public when hosted. Visibility into commercial usage.
- Reciprocal contribution: improvements to forks must be available to upstream.
- Inclusion of GPL-3.0 code is permitted under GPL-3.0 §13 (also confirmed in audit Section A — useful for borrowing patterns from portfoliomanager if ever needed).

### Foreclosed

- Permissive use in proprietary closed-source products (rejected; this was the goal).
- Combination with non-AGPL-compatible code.

## References

- [GNU AGPL-3.0 license text](https://www.gnu.org/licenses/agpl-3.0.txt)
- AGPL-3.0 §13 (network use clause)
- [ADR-0001 — Greenfield over forking portfoliomanager](0001-greenfield-over-portfoliomanager.md)
- [ADR-0003 — License clause: AGPL-3.0-or-later](0003-license-clause-or-later.md)
