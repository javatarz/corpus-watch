# ADR-0006: Database — SQLite single-file

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch is a self-hosted, single-tenant-per-household application (see [ADR-0007](0007-self-hosted-single-tenant.md)). It stores transactions, holdings, snapshots, prices, and configuration. Scale: low — one household, perhaps tens of thousands of rows over many years. Concurrency: low — one user (or a few family members) at a time.

The user has explicitly asked for an "easily exportable database."

## Options considered

1. **SQLite** — file-based, zero ops, embedded in process. Modern SQLite supports JSON, FTS, CTEs, window functions, partial indexes, generated columns. WAL mode handles concurrent reads with one writer.
2. **PostgreSQL** — full RDBMS. More features (full-text, complex types, replication), but requires a separate server process. Heavier ops burden for self-hosted users.
3. **DuckDB** — analytics-focused embedded DB. Single file, columnar. Less mature for OLTP; not designed for frequent writes.
4. **MariaDB / MySQL** — same trade-offs as Postgres without the same advantages. Rejected.

## Decision

**SQLite single-file database. WAL mode enabled. SQLAlchemy abstracts the dialect for future migration.**

### Reasons

- **Zero ops.** No DB server process to start, monitor, back up separately. SQLite file lives in a Docker volume.
- **Backup = file copy.** Trivially aligns with the export requirement. SQLite's online backup API can produce consistent snapshots without quiescing.
- **Modern SQLite is enough.** JSON1, FTS5, CTEs, window functions, partial indexes — sufficient for our queries. Decimal precision via `NUMERIC` storage class.
- **Single-writer is fine for our model.** A household has one or two concurrent users at most; WAL mode handles that comfortably.
- **Resource footprint.** Embedded; no separate process. Saves ~50–100 MB RAM vs Postgres on a home server.
- **Migration path exists.** SQLAlchemy lets us swap to Postgres if scale ever demands. Abstract over dialect-specific features at the data-access layer.

## Consequences

### Accepted

- **Single-writer constraint.** Concurrent write-heavy workloads will queue. Acceptable: corpus-watch is read-mostly; writes are bulk imports (CAS, NPS, EPF) followed by user-driven CRUD. No write contention expected.
- **No replication.** Acceptable for self-hosted single-tenant. User backups via export feature (see SCOPE).
- **No native arrays / advanced types.** Use JSON columns (SQLite supports JSON1 ext) where needed. Acceptable for our data model.
- **Decimal handling care needed.** SQLite stores `NUMERIC` as either INTEGER, REAL, or TEXT. Use `Decimal` in Python and standardise on a conversion pattern in the data layer.

### Enabled

- One-file backup. One-file export (matches the "easily exportable database" requirement directly).
- Cheap test fixtures: each test gets a fresh in-memory SQLite DB.
- Deployment simplicity: `docker compose up` brings the entire system up; no DB-init dance.
- Self-hosted users on Raspberry Pi-class hardware can run corpus-watch without provisioning a separate DB.

### Foreclosed

- True concurrent multi-user write workloads. Not in scope.
- Postgres-specific features (advisory locks, native partitioning, listen/notify). If we need them, the migration path via SQLAlchemy is viable.

## References

- [SQLite WAL mode](https://www.sqlite.org/wal.html)
- [SQLite "Appropriate uses for SQLite"](https://www.sqlite.org/whentouse.html)
- [SQLAlchemy 2.x dialect docs](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)
- [ADR-0005 — Backend stack](0005-backend-stack.md)
- [ADR-0007 — Self-hosted, single-tenant deployment](0007-self-hosted-single-tenant.md)
