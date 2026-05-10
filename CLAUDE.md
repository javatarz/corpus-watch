# corpus-watch — Claude Code Context

Privacy-focused, self-hosted, FOSS net worth tracker for Indian DIY investors and their families.

See [docs/VISION.md](docs/VISION.md) for the full vision and [docs/SCOPE.md](docs/SCOPE.md) for MVP and post-MVP scope.

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, SQLite, Alembic for migrations
- **Frontend**: React + Vite + TypeScript. CDN-fetched libs permitted under conditions (see "Frontend asset loading" below). Bundling preferred.
- **Charting**: Recharts (or similar; pick at first chart card)
- **Background jobs**: FastAPI `BackgroundTasks` for in-process async refresh; no external job queue
- **Packaging**: `pyproject.toml`, `uv` for env management
- **Lint/format**: `ruff` (lint + format)
- **Type check**: `mypy --strict` on backend, `tsc --strict` on frontend
- **Tests**: `pytest` for backend (real SQLite test DB, not mocks for the DB layer); `vitest` for frontend
- **CI**: GitHub Actions from day one. Lint + typecheck + test on every PR.
- **Container**: Docker + Docker Compose. Single `docker compose up`.
- **License**: AGPL-3.0.

## Reuse — vetted libraries (from portfoliomanager audit)

- `casparser` (MIT) — CAS PDF parsing for CAMS + KFintech
- `pyxirr` (Apache-2.0) — XIRR, faster than scipy
- `mftool` — fallback MF NAV utilities (AMFI direct is primary)
- `yfinance` — stock EOD prices via Yahoo

All AGPL-3.0 compatible. No paid APIs.

## Frontend asset loading

CDN-fetched libraries permitted **only if all of these hold**:

1. **Version-locked.** No `latest`, no major-version floats. Pin to exact semver.
2. **Subresource Integrity (SRI).** Every `<script>` and `<link>` tag carries `integrity="sha384-..."`. Browser refuses to execute on hash mismatch — this is what defends against supply-chain compromise of the CDN.
3. **CDN provider listed here.** Approved providers: jsdelivr, cdnjs, unpkg. Add to this list via PR if a new one is justified.

**Bundle preferred for JS/CSS code.** With Vite, bundling is zero-cost (already in `node_modules`); skip the CDN unless it solves a real problem. CDN is acceptable for static assets (fonts, icons) where self-hosting adds friction.

**Threat model.** CDN provider sees IP + Referer, not user financial data — that lives in SQLite, never sent to the CDN. Confidentiality risk is supply-chain compromise of the served asset; SRI mitigates this.

## Traps to avoid (lessons from portfoliomanager audit — see ADR-0001)

- **No plaintext secrets on disk.** CAS PDF passwords, future API keys → OS keyring or encrypted at rest.
- **No phone-home pings.** Zero outgoing calls except documented price feeds.
- **No hardcoded asset-class fan-out.** Use registry/plugin pattern from day one. Adding an asset class must touch ≤2 files plus a new asset module.
- **No Selenium-pinned-browser tests.** Backend via pytest. Frontend via vitest + React Testing Library. E2E (if added) via Playwright with bundled browser.
- **No schema typos baked in.** Code review catches misspelled column names.
- **No hidden runtime deps** (e.g., JVM via Tika). Pure Python + JS.

## Code standards

- Type hints mandatory on public functions. `mypy --strict` clean.
- Docstrings only when *why* is non-obvious. No what-the-code-does narration.
- No comments referencing tasks, fixes, callers, or PRs.
- No backwards-compat shims unless externally facing.
- Validate at boundaries; trust internals.
- Small, focused commits. Imperative subject, ≤50 chars. Reference issue with `#N`.
- Conventional commit verb prefixes (`Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Rename`, `Move`, `Docs`, `Test`, `Config`).

## Ethos

- **Privacy is the product.** When in doubt, less data movement.
- **Lean MVP, fast iteration.** Reject features that don't earn complexity.
- **Family-first schema.** Even if v1 UI is single-person.
- **Configurability over defaults.** Defaults sensible, not opinionated.
- **Reuse > reinvent.**

## Working agreement with Claude

- **Step-by-step.** No actions (file writes, repo init, commits, gh ops) without explicit asking first.
- Plan before implementing for non-trivial tasks.
- When recommending a library or feature, verify it exists and fits — don't trust training-data memory.
- Prefer editing files over creating; prefer simple over abstract.
- Backlog lives on GitHub Issues at `javatarz/corpus-watch`. Refer to issues by number; do not introduce a new local backlog file.
- **Proactively prompt for ADRs.** When a decision in conversation matches ADR criteria — alternatives debated, hard to reverse, encodes a non-obvious constraint, or a future contributor will ask "why this way?" — surface it before moving on. Suggest writing one and propose the ADR title. Do not silently let a decision-shaped conversation pass without capture. See [docs/adr/README.md](docs/adr/README.md) for criteria and template.

## Story shape — INVEST + vertical slicing

Every backlog card must be:

- **Independent** — minimal cross-card ordering; no "must do X first" trains.
- **Negotiable** — body lists scope but invites trade-offs.
- **Valuable** — a real user can demo the outcome. No "schema PR", no "skeleton PR", no horizontal layer cards.
- **Estimable** — sized XS/S/M/L; if you can't size it, it's underspecified.
- **Small** — L is the ceiling. Anything bigger gets split.
- **Testable** — acceptance is observable behaviour, not "tests pass".

And **vertically sliced** — each card cuts thin through every layer it touches (DB → API → UI → Docker), delivering one user-observable behaviour. The first slice pays the infra tax (skeletons, baseline migration, compose file). Later slices extend each layer as features earn it. No layer-only foundation cards; if a card is "set up X", it's wrong — fold it into the first slice that needs X.

Reuse card numbers when scope drifts; empty obsolete cards into shells with title `TBD` and label `available` rather than closing.

When grooming or proposing cards, apply this shape without being asked. Reject horizontal-layer cards on sight.

## Repo layout

```
corpus-watch/
  CLAUDE.md           # this file
  README.md           # public-facing pitch + quickstart (created in repo-init card)
  LICENSE             # AGPL-3.0 (created in repo-init card)
  pyproject.toml      # (created in repo-init card)
  docs/
    VISION.md
    SCOPE.md
    adr/
      README.md       # ADR conventions + index
      0001-greenfield-over-portfoliomanager.md
    eval/
      portfoliomanager-AUDIT.md
  src/                # backend (created later)
  web/                # frontend (created later)
  tests/              # backend tests (created later)
```

## Project meta

- GitHub: `javatarz/corpus-watch` (public, AGPL-3.0; created in repo-init card)
- Owner: solo dev (Priya)
- Greenfield over portfoliomanager: see [ADR-0001](docs/adr/0001-greenfield-over-portfoliomanager.md)
