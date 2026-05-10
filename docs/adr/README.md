# Architecture Decision Records

ADRs capture significant architectural or product decisions, the context behind them, the alternatives considered, and the consequences accepted.

## Format

Each ADR is a markdown file named `NNNN-short-slug.md`, where `NNNN` is a zero-padded sequence number. Numbers are immutable once assigned, even if the ADR is later superseded.

### Template

```markdown
# ADR-NNNN: Title

- **Status**: Proposed | Accepted | Superseded by ADR-XXXX | Deprecated
- **Date**: YYYY-MM-DD

## Context

What problem are we solving? What constraints exist?

## Options considered

1. Option A — pros, cons
2. Option B — pros, cons
3. Option C — pros, cons

## Decision

What we chose, and why.

## Consequences

What this enables, what this forecloses, what we accept as cost.

## References

Links to evidence, prior art, supporting docs.
```

## When to write an ADR

Write one when the decision:

- Is hard to reverse later (data model, license, framework, deployment shape)
- Will be questioned by future contributors ("why did we do it this way?")
- Trades off between clearly-named alternatives
- Encodes a non-obvious constraint

Don't write one for routine implementation choices that can be refactored cheaply.

## Index

- [0001 — Greenfield over forking portfoliomanager](0001-greenfield-over-portfoliomanager.md)
- [0002 — Frontend asset loading policy](0002-frontend-asset-loading.md)
- [0003 — License clause: AGPL-3.0-or-later](0003-license-clause-or-later.md)
- [0004 — License family: AGPL-3.0](0004-license-agpl-3-0.md)
- [0005 — Backend stack: Python, FastAPI, SQLAlchemy](0005-backend-stack.md)
- [0006 — Database: SQLite single-file](0006-database-sqlite.md)
- [0007 — Self-hosted, single-tenant deployment](0007-self-hosted-single-tenant.md)
- [0008 — Refresh strategy: lazy with 24h TTL, no cron](0008-refresh-strategy-lazy-ttl.md)
- [0009 — Family-first data model](0009-family-first-data-model.md)
- [0010 — Frontend stack: React + Vite + TypeScript bundle](0010-frontend-stack.md)
