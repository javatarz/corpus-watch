# ADR-0009: Family-first data model

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch's positioning is family-aware: a household — couple plus children, or other group of individuals — should share one canonical net worth view, while assets remain attributable to specific individuals (PPF and SSY accounts cannot be jointly held; MF folios usually have a primary holder; spouses still have separate EPF accounts).

The MVP UI shows a single individual to keep scope tight, but the schema decision is hard to reverse: once data accumulates against a single-individual model, retrofitting a household layer requires migrating every asset row, every transaction, every query.

The portfoliomanager audit ([ADR-0001](0001-greenfield-over-portfoliomanager.md), Section C) flagged this as one of three load-bearing reasons for greenfield: portfoliomanager has a `User` (Person) entity but no `Household`, and login accounts see all Persons. That shape leaves the family question half-answered.

## Options considered

1. **Individual-only schema.** Simplest model. Bolting on a `Household` later requires migrating all FK columns, query scopes, and forms.
2. **Family-first schema from day one.** `Household → Individual → Account → Asset → Transaction/Snapshot`. UI may show a single Individual in MVP; schema supports many.
3. **Hybrid.** Start individual-only, add a `group_id` later. Worst of both: existing rows have no group, new rows have one, queries fork.

## Decision

**Family-first schema from day one. UI surfaces one Individual within a Household of size 1 in MVP. Schema supports many Individuals per Household and many Households per deployment (though deployment is single-tenant, so one Household per instance is the expected shape — see [ADR-0007](0007-self-hosted-single-tenant.md)).**

### Schema sketch

```
Household (id, name, created_at, ...)
  └── Individual (id, household_id FK, name, dob, ...)
        └── Account (id, individual_id FK, asset_class_code, broker, ...)
              └── Asset (id, account_id FK, scheme_code, ...)
                    ├── Transaction (id, asset_id FK, date, type, units, amount, ...)
                    └── Snapshot (id, asset_id FK, ts, value, ...)
```

Every query scopes by `household_id` (enforced at the repository / session layer, not relied on in handlers).

### Reasons

- **Indian household reality.** Joint planning is the norm. Goals like "₹X for child's education in 2042" cross individual ledgers.
- **Migration cost from individual-only is high.** Every query gets a join, every form a household selector, every export a scope. Cheaper to add the layer up front.
- **Asset attribution remains per-Individual.** Schema doesn't conflate ownership with shared view. Joint-held assets (rare in India: HUF accounts, joint MF folios) modelled as multiple ownership rows post-MVP if needed.
- **Aligns with audit lesson.** portfoliomanager's lack of true household entity created friction we explicitly avoid (audit Section C).

## Consequences

### Accepted

- Schema is slightly more complex from commit 1: one extra entity (`Household`), one extra FK column on `Individual`. Marginal cost, paid once.
- All queries must scope by `household_id`. Enforced at the repository layer and in tests.
- Initial UI hides the household concept (single-individual MVP). Slightly more setup code for the "default household of one" case.

### Enabled

- Family-shared dashboards in post-MVP without schema migration.
- Goals across individuals (child's education, parents' care) modelled cleanly.
- Per-Individual XIRR, household XIRR, per-Individual net worth, household net worth — all natural queries.
- Multi-Individual auth (post-MVP) layered on top of an existing structure.

### Foreclosed

- Treating an `Individual` as the top-level entity (would have been simpler in single-person UI).
- Rationalising "one user = one Person" (we deliberately separate the two from the start).

## References

- [VISION.md](../VISION.md) § Family-aware
- [SCOPE.md](../SCOPE.md) § Data
- [ADR-0001 — Greenfield over forking portfoliomanager](0001-greenfield-over-portfoliomanager.md) § Reasons #2
- [ADR-0007 — Self-hosted, single-tenant deployment](0007-self-hosted-single-tenant.md)
