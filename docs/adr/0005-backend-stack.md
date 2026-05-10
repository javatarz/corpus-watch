# ADR-0005: Backend stack — Python, FastAPI, SQLAlchemy

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch needs a backend that ingests Indian-finance data (CAS PDFs, NPS statements, EPF passbooks), refreshes prices from public feeds, computes returns and projections, and serves an HTTP API to the React frontend. It will run on a self-hosted home server with constrained resources (Raspberry Pi-class to small NAS).

The user is fluent in Python and offered Kotlin + Spring Boot as an alternative.

The portfoliomanager audit ([ADR-0001](0001-greenfield-over-portfoliomanager.md) Section A) confirmed that the Indian-finance ecosystem is overwhelmingly Python-native: `casparser` (CAS PDFs), `pyxirr` (XIRR), `mftool` (NAVs), `yfinance` (stocks).

## Options considered

1. **Python + FastAPI + SQLAlchemy** — leverages native Indian-finance ecosystem. Modern, async, low boilerplate. SQLAlchemy 2.x has type-checked ORM. Lightweight runtime.
2. **Kotlin + Spring Boot** — user's original suggestion. Robust, enterprise-grade. JVM RAM footprint heavy on home server. `casparser` and friends require subprocess invocation or porting.
3. **Go + chi/gin** — fast, single-binary deploy. Worse ecosystem for PDF parsing and Indian-finance utilities. Higher effort to port the equivalent of `casparser`.
4. **Node + Hono/Fastify** — same language as frontend (TypeScript). Worse for finance libs; less mature scientific computing.
5. **Rust + Axum** — fast, low memory. Slow dev velocity for solo MVP; finance ecosystem thin.

## Decision

**Python 3.12+ with FastAPI and SQLAlchemy 2.x. `uv` for environment and packaging. Alembic for migrations.**

### Reasons

- **Ecosystem fit.** `casparser`, `pyxirr`, `mftool`, `yfinance` are mature Python libraries. Using them natively avoids subprocess wrappers or third-party REST APIs (which would also break the privacy posture).
- **FastAPI**: modern async framework; types via Pydantic; OpenAPI generated automatically (consumed by frontend client codegen); minimal boilerplate; strong typing throughout.
- **SQLAlchemy 2.x**: typed ORM (`Mapped[T]`), no implicit magic; pairs cleanly with Alembic for migrations; supports SQLite first-class.
- **Resource footprint.** Python web app baseline ~80–150 MB RAM; comfortable on home server. JVM (Spring Boot) baseline 300–500 MB; uncomfortable on Raspberry Pi-class hardware.
- **Solo-dev velocity.** Python's lower boilerplate matters more than Kotlin's compile-time guarantees for a one-person project. Type hints + `mypy --strict` close the safety gap meaningfully.
- **`uv` for env and packaging.** Fast (Rust), reliable, lockfile-first; replaces pip/pip-tools/poetry/virtualenv with one tool. Boring choice with momentum.

## Consequences

### Accepted

- Python's runtime is slower than JVM for compute-bound workloads. Acceptable: corpus-watch is I/O-bound (DB, HTTP fetch, file parse), not CPU-bound. Hot loops (XIRR via `pyxirr` is Rust-backed) are already optimised.
- GIL constraint on threading. Mitigated by FastAPI's async + small data scale (one household).

### Enabled

- Direct use of vetted Indian-finance libraries; zero porting cost.
- Type-checked codebase (`mypy --strict`) with low boilerplate.
- Auto-generated OpenAPI; typed frontend client via codegen.
- Standard Docker deployment; small image; fast startup.
- Boring tooling: `pytest`, `ruff`, `mypy`, `alembic`, `uv` — all well-documented, well-supported.

### Foreclosed

- JVM ecosystem (Spring, Hibernate, etc.). Cost: minor; the user is fluent in Python.
- Single-binary deploy (Go-style). Mitigated by Docker.

## References

- [`casparser`](https://github.com/codereverser/casparser)
- [`pyxirr`](https://github.com/Anexen/pyxirr)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.x typing guide](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [`uv`](https://github.com/astral-sh/uv)
- [ADR-0001 — Greenfield over forking portfoliomanager](0001-greenfield-over-portfoliomanager.md) — audit confirms ecosystem fit
