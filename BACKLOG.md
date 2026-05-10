# Backlog (temporary)

This file is the seed list for GitHub Issues. Once the repo is initialised and these are migrated to issues, **this file is deleted**.

Order = rough priority. T-shirt size: **S** ≤ 4h, **M** 1–2 days, **L** 2–5 days, **XL** > 5 days.

---

## Setup phase

### 1. Repo init [M]
- `git init`, default branch `main`
- `gh repo create javatarz/corpus-watch --public --description "<draft>"`
- Repo description draft: `"Privacy-focused, self-hosted net worth tracker for Indian DIY investors and families. AGPL-3.0."`
- Topics: `personal-finance`, `india`, `networth`, `self-hosted`, `privacy`, `agpl`, `python`, `fastapi`, `react`
- Configure GH project board: backlog → todo → in progress → review → done
- LICENSE file (AGPL-3.0 full text)
- `pyproject.toml` skeleton (Python 3.12, ruff, mypy, pytest, uv-managed)
- `.gitignore` (Python, Node, OS, IDEs, `*.sqlite`)
- `README.md` skeleton (pitch + quickstart placeholder + links to docs)
- `web/` Vite + React + TS skeleton with `package.json` (zero CDN deps)
- GH Actions workflow: `lint + typecheck + test` on push and PR
- Default labels: `type:feat`, `type:bug`, `type:chore`, `type:docs`, `area:ingest`, `area:ui`, `area:projection`, `area:audit`, `area:infra`, `priority:p0..p3`
- First commit, push, verify CI green

### 2. Migrate backlog to GH issues [S]
- Create one issue per card 3+ below, with title, body, labels, size
- Add issues to the project board
- Delete `BACKLOG.md`
- Update `CLAUDE.md` to remove `BACKLOG.md` reference

---

## Foundation

### 3. Data model + migrations [L]
- Schema: `Household`, `Individual`, `Account`, `AssetClass` (registry), `Asset`, `Transaction`, `Snapshot`, `PriceQuote`
- Asset-class registry pattern (no hardcoded fan-out)
- Alembic baseline migration
- SQLAlchemy models with type hints
- Tests: schema integrity, fixtures factory

### 4. Backend skeleton [M]
- FastAPI app structure (routers, deps, settings via `pydantic-settings`)
- SQLite session lifecycle
- Health endpoint
- Error handler middleware
- Tests: app boots, health endpoint green

### 5. Frontend skeleton [M]
- Vite + React + TS + Tailwind (no CDN)
- Routing (`react-router`)
- Layout shell (header, sidebar, content)
- Typed API client (openapi-codegen or hand-written)
- Empty-state component for net worth screen

---

## Ingestion

### 6. AMFI NAV refresh [M]
- Fetch `NAVAll.txt`, parse, upsert into `PriceQuote`
- Lazy refresh with 24h TTL
- Async via `BackgroundTasks` on dashboard hit
- Tests: parse fixture, idempotent upsert

### 7. Yahoo Finance EOD stock prices [M]
- `yfinance` integration; bulk fetch
- Same lazy/TTL pattern as AMFI
- Tests with cassette/fixture

### 8. CAS PDF import (CAMS + KFintech) [L]
- `casparser` integration
- Map CAS schemes → `Asset`, transactions → `Transaction`
- Idempotency key: folio + scheme + date + amount + type + units
- Upload UI, password prompt, parse → preview → commit
- Tests against anonymised sample CAS PDFs

### 9. NPS Transaction Statement PDF import [L]
- Custom parser (no good library found)
- Protean + KFintech CRA layouts
- Tests against fixture PDFs

### 10. EPF passbook PDF import [L]
- Custom parser
- Tests against fixture PDFs

### 11. Manual FD entry [S]
- CRUD UI for FDs (bank, principal, rate, start, maturity, payout type)
- Snapshot generation on save

---

## Views

### 12. Net worth aggregate dashboard [M]
- Sum across all assets, all individuals
- Per-asset-class breakdown chart
- Per-individual breakdown chart
- Net worth time-series chart

### 13. Asset class drill-down [M]
- List assets in class, sortable
- Per-asset value, % of class, % of net worth

### 14. Asset detail page [M]
- Value-over-time chart
- Transaction history
- Per-asset XIRR

---

## Returns

### 15. XIRR calculation [M]
- `pyxirr` integration
- Per asset, per individual, per household
- Cached, invalidated on transaction change

---

## Projection

### 16. Projection engine [L]
- Configurable global inflation rate
- Configurable per-asset-class expected return
- Time-value math, monthly compounding
- Per-individual + household projection
- UI: settings page for rates; projection chart on dashboard

---

## Audit feature

### 17. Expected contribution config [S]
- UI to declare expected monthly contribution per NPS/EPF account
- Schema: `ExpectedContribution(account_id, amount, cadence_days, expected_day_of_month)`

### 18. Missed-deposit detection [M]
- Heuristic: scan snapshots, detect expected increase, warn if absent
- In-app banner on dashboard + asset detail page
- Tests: simulated snapshot timelines

---

## Export

### 19. Database export [S]
- SQLite file copy endpoint (download)
- JSON dump per entity (download)

---

## Operational

### 20. Docker Compose [M]
- Single `docker compose up` brings up backend + frontend (or backend serves built frontend behind nginx)
- Volume for SQLite file
- README quickstart updated

### 21. Documentation pass [S]
- README polish: pitch, screenshot, quickstart
- VISION/SCOPE link audit
- First user-visible release notes
