# corpus-watch

Privacy-focused, self-hosted net worth tracker for Indian DIY investors and their families.

> **Status:** Pre-alpha. Active development. No usable build yet.

## What this is

A FOSS tool for Indians to see all their investments — mutual funds, stocks, EPF, NPS, FDs, and more — in one self-hosted dashboard. No third party sees your data. Works for individuals or households.

## Why

Existing tools (INDmoney, Smallcase, Groww, etc.) read your data and monetise it. The Account Aggregator framework requires an FIU NBFC licence — out of reach for individuals. corpus-watch fills that gap with a privacy-first, family-aware alternative.

## Documentation

- [Vision](docs/VISION.md)
- [Scope](docs/SCOPE.md)
- [Architecture Decision Records](docs/adr/)

## Development

Backend: Python 3.12+, FastAPI, SQLAlchemy, SQLite. Frontend: React + Vite + TypeScript. Managed with [`uv`](https://github.com/astral-sh/uv).

```sh
uv sync --extra dev
uv run pytest
```

Frontend skeleton lives under `web/` (see `web/README.md` once created).

## License

[AGPL-3.0-or-later](LICENSE).
