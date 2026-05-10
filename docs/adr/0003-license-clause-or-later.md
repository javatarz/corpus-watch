# ADR-0003: License clause — AGPL-3.0-or-later

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch is licensed AGPL-3.0 (decided in [ADR-0001](0001-greenfield-over-portfoliomanager.md)). The AGPL family has two SPDX license expressions:

- `AGPL-3.0-only` — locks the project to AGPL version 3 specifically. A future FSF-published version (a hypothetical AGPL-4) does not auto-apply to this codebase.
- `AGPL-3.0-or-later` — permits licensees to choose any later version of AGPL published by the FSF. Future FSF revisions effectively flow through to derivative works at the licensee's option.

The choice is hard to reverse once external contributors arrive. Re-licensing requires the consent of every copyright holder. Picking it now, before any external contribution, is the cheap moment.

## Options considered

1. **`AGPL-3.0-only`** — pessimistic about future FSF revisions; commits to v3 forever. Useful if a hypothetical v4 might weaken protections in a direction we don't accept.
2. **`AGPL-3.0-or-later`** — optimistic about FSF stewardship; allows future revisions to apply. Standard FSF guidance recommends "or-later" for most projects.
3. **No clause** — drop the version qualifier entirely. Rejected: leaves licensees uncertain about which version applies.

## Decision

**`AGPL-3.0-or-later`.**

### Reasons

- FSF's own guidance recommends "or-later" so the broader free-software ecosystem can evolve in lockstep.
- Future AGPL revisions are likely to address emerging issues (e.g., AI training, network-equivalent activities) without weakening core protections. We want those updates to flow through.
- Re-licensing later (post-contributor) is effectively impossible without unanimous consent. "or-later" preserves option value cheaply now.
- Major peer projects in the privacy / self-hosted space (Ghostfolio, Sure, Mastodon) use AGPL-3.0-or-later. Aligning reduces ecosystem friction.

## Consequences

### Accepted

- Codebase is bound by future FSF revisions if licensees opt into them. We trust the FSF's stewardship of the AGPL family.

### Enabled

- Smooth interaction with the broader AGPL ecosystem.
- Future flexibility without unanimous re-licensing.

### Foreclosed

- Pinning the licence to v3 forever in case a future revision proves unacceptable.

## Implementation

- `LICENSE` file: verbatim GNU AGPL-3.0 text from FSF.
- `pyproject.toml` `license` field: `"AGPL-3.0-or-later"` (SPDX expression).
- `README.md` references `AGPL-3.0-or-later`.
- Source-file headers (added when source files arrive) note `AGPL-3.0-or-later`.

## References

- [GNU AGPL-3.0 license text](https://www.gnu.org/licenses/agpl-3.0.txt)
- [FSF — How to choose a license for your own work](https://www.gnu.org/licenses/license-recommendations.html)
- [SPDX license expressions](https://spdx.dev/learn/handling-license-info/)
- [ADR-0001 — Greenfield over forking portfoliomanager](0001-greenfield-over-portfoliomanager.md)
