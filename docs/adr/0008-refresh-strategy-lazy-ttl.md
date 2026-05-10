# ADR-0008: Refresh strategy — lazy with 24h TTL, no cron

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch displays mutual fund NAVs (from AMFI), stock EOD prices (from Yahoo Finance), and any other periodic price data. The user's stated requirement: holdings should be "as up to date as possible" while avoiding unnecessary scheduling complexity. They explicitly asked whether to use a cron or fetch on page load.

Cadence of source data:
- AMFI NAV: daily, single text file at `https://www.amfiindia.com/spages/NAVAll.txt` covering all funds.
- Yahoo Finance EOD: daily per stock.
- CAS / NPS / EPF: imported manually, not fetched on a schedule.

## Options considered

1. **Cron-driven refresh.** A scheduled job (Huey, Celery beat, OS cron) hits each source on a fixed cadence. Reliable, predictable. Cost: separate scheduler process, silent failure mode for missed jobs, fetches during idle hours, schedule management.
2. **Eager on every page load.** Fetch on every dashboard hit. Simple. Wastes bandwidth, slows page load, hammers external sources unnecessarily.
3. **Lazy with TTL.** On dashboard load, check `last_refreshed_at` per source. If stale (>TTL), kick an async background refresh; render cached values immediately. No cron, no missed jobs.
4. **Hybrid — lazy by default, cron opt-in.** Best of both, but doubles the surface area in MVP.

## Decision

**Lazy refresh with 24-hour TTL. Async background fetch via FastAPI `BackgroundTasks` triggered on dashboard load. No cron in MVP.**

### Reasons

- **Self-hosted personal tool, low traffic.** A typical user opens the dashboard zero to a few times per day. Pre-warming when no one is looking is wasted work.
- **No scheduler = simpler ops.** No Huey/Celery process, no scheduler-related failure modes, no "did the cron run?" questions. One less moving part for self-hosted users.
- **Single-fetch sources are cheap.** AMFI NAVAll is one HTTP fetch covering all funds. Stock prices via `yfinance` batch. Refreshing on user action is fast enough that the lazy pattern is invisible.
- **Render cached, refresh in background.** Dashboard renders the previous snapshot instantly; the next load (or a WebSocket push, post-MVP) shows the freshly fetched data. Zero perceived latency.
- **24-hour TTL matches source cadence.** AMFI publishes daily. EOD is daily. There is nothing fresher to fetch within a day.
- **Failure semantics are obvious.** If AMFI is down, the user sees the cached value with a "last refreshed at <timestamp>" note. No silent failed cron run.

## Consequences

### Accepted

- The first load after a long absence shows briefly stale data (the previous snapshot) while the background refresh runs. UI surfaces the staleness indicator; refresh completes within seconds.
- No pre-warming. If a user opens the dashboard at 7am and AMFI publishes at 11pm, they will see yesterday's NAV. Acceptable for our purpose.
- Background tasks live in-process. If the FastAPI server is restarting when a refresh is queued, it is dropped. Acceptable: the next dashboard load triggers a fresh fetch.

### Enabled

- Single-process deployment. No scheduler.
- Trivial Docker Compose: one backend container, one frontend container (or one combined).
- Easy to reason about: the refresh you see was triggered by a user action.
- Cron pre-warming can be added post-MVP as an opt-in (see [SCOPE.md](../SCOPE.md) post-MVP themes) without changing the core refresh logic.

### Foreclosed

- True up-to-the-second tickers. Out of scope; daily granularity is sufficient.
- Pre-computed analytics that depend on always-fresh data. Acceptable; analytics are computed on the cached snapshot.

## References

- [SCOPE.md](../SCOPE.md) — MVP refresh requirement
- [FastAPI BackgroundTasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- AMFI NAV daily file — `https://www.amfiindia.com/spages/NAVAll.txt`
