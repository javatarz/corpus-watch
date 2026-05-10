# Scope

## MVP — must-have for v1

### Ingestion
- CAS PDF import (CAMS + KFintech via `casparser`); covers mutual funds + NSDL/CDSL stocks
- NPS Transaction Statement PDF import (Protean + KFintech CRA)
- EPF passbook PDF import
- Manual entry: fixed deposits
- Idempotent re-import (transaction-level dedupe via stable identity key)

### Pricing
- AMFI NAV refresh from `https://www.amfiindia.com/spages/NAVAll.txt` — single fetch covers all funds
- Stock EOD prices via Yahoo Finance (`yfinance`)
- Lazy refresh with 24h TTL, async background on dashboard load. **No cron.**

### Views
- Aggregate net worth (household-level)
- Per-individual net worth
- Per-asset-class drill-down
- Per-asset (e.g., one MF scheme) drill-down with value-over-time chart
- Net worth time-series chart

### Audit feature (MVP version)
- User declares expected monthly contribution per NPS/EPF account
- Tool tracks value snapshots over time
- In-app warning if expected contribution didn't materialise within window of expected debit date

### Returns
- XIRR per asset, per individual, per household (via `pyxirr`, derived from CAS history)

### Projection
- Configurable global inflation rate
- Configurable per-asset-class expected return
- Time-value future projection of net worth

### Data
- SQLite single-file DB
- Family-aware schema: `Household → Individual → Account → Asset → Transaction/Snapshot`
- Asset class via registry pattern (extensible — avoid portfoliomanager's hardcoded fan-out, see [ADR-0001](adr/0001-greenfield-over-portfoliomanager.md))
- Export: SQLite file copy + JSON dump per entity

### Onboarding & UX
- Empty net worth screen with prompts to add first asset
- In-app banner for warnings/reminders only

### Operational
- Single `docker compose up`
- No auth in MVP (single-tenant home server)
- AGPL-3.0 license file
- README, CLAUDE.md, ADRs, this scope doc

## Post-MVP — themes (unordered)

### Goals
- Goal entity (retirement default, custom types)
- Future-value vs present-value entry modes
- Per-goal inflation override
- FIRE goal with detailed math (future-expense-aware, medical, lifestyle)
- Backward planning (given goal, compute required SIP/lumpsum)
- Multi-goal prioritisation

### Liabilities
- Home loan, car loan tracking
- Net worth = assets − liabilities
- EMI schedule, principal vs interest split

### Tax
- LTCG/STCG basis tracking
- 80C / 80D / 80CCD utilisation across household
- Indexation for debt funds
- Surcharge thresholds

### Asset classes
- ESOP / RSU with vesting + USD conversion
- Multi-currency support
- Crypto via exchange APIs
- ULIP / endowment treatment
- Real estate with valuation refresh
- Cash / savings account

### Analytics
- Asset allocation drift + rebalancing nudges
- Monte Carlo projection
- What-if scenarios (job loss, market crash, salary jump)
- Withdrawal phase modelling (4% rule, bucket strategy)
- Sequence-of-returns risk

### Audit (deeper)
- Validate exact deposit amounts vs declared expected
- Cross-check employer EPF contribution rate
- NPS asset-class breakup drift detection

### Quality of life
- Email / push reminder delivery
- Multi-user auth (per-individual login within household)
- Cron-based pre-warm refresh (replace lazy)
- Mobile-native app

## Explicit non-goals

Tax filing. Robo-advisory. SEBI/RBI-regulated activities. Insurance gap analysis. Multi-tenant SaaS.

(See also [VISION.md](VISION.md) § Non-goals.)
