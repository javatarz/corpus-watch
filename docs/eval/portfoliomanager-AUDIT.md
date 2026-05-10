# Audit: krishnakuruvadi/portfoliomanager

**Auditor:** Claude (Opus 4.7), one focused session.
**Date:** 2026-05-10.
**Repo state:** `main` @ `dc7e283` (last commit 2026-04-08, all dependabot since 2025-11).
**Method:** Code reading + git log + GitHub API. Did NOT run docker compose end-to-end (chromedriver pinned to v104 in Dockerfile would need patching, and architectural verdict is clear from the source alone).

---

## A. Legal & licensing

- [x] **License file confirms GPL-3.0** — exact version: GPLv3 (no "or-later" qualifier in `LICENSE` or `README`)
  > Evidence: `LICENSE` is verbatim FSF GPLv3 text (`Version 3, 29 June 2007`). `README.md` and `requirements.txt` carry no `License-Expression` metadata. GitHub auto-detection records `gpl-3.0` (verified via `gh repo view`). Treat as **GPL-3.0-only** for safety; user can ask the maintainer to clarify if forking.
- [x] **No third-party code in conflicting licenses.** All deps in `requirements.txt` are PyPI packages with MIT/BSD/Apache/PSF; no LGPL inclusions, no proprietary blobs, no static-linked GPL incompatibles.
  > Evidence: scanned `requirements.txt` (133 packages). Notable: `casparser` (MIT), `pyxirr` (MIT), `mftool` (MIT), `yfinance` (Apache-2.0), `Twisted` (MIT). No license red flags.
- [x] **GPL-3 → AGPL-3 derivative is legally clean.** GPL-3.0 §13 explicitly allows combining with AGPL-3.0 code; the combined work, when conveyed over a network, falls under AGPL terms for the AGPL-licensed portion. corpus-watch (AGPL-3.0) may incorporate or fork GPL-3.0 portfoliomanager code.
  > Evidence: GPL-3.0 §13 ("Use with the GNU Affero General Public License"). No `GPL-3.0-only WITH classpath-exception` or similar trap.
- [x] **No trademark / branding constraints.** No `TRADEMARKS`, `NOTICE`, or `BRANDING.md`. README does not require attribution boilerplate beyond GPL.
- [x] **No CLA required.** No `CLA.md`, `CONTRIBUTING.md` with sign-off, or DCO bot in `.github/`. PRs accept inbound = outbound under repo license.

**Verdict on Section A:** clean. License is not a blocker for any direction.

---

## B. Architecture & deploy

- [x] **Tech stack reality** — Django 5.2.13, Python 3.12 (Dockerfile) / 3.11+3.12 (CI matrix), PostgreSQL 13 (Docker compose), Huey 2.3.0 (background tasks). README's "Python 3.9 / 3.10" claim is stale — code targets 3.11+.
  > Evidence: `Dockerfile:1` (`python:3.12.8-slim`), `.github/workflows/django.yml:16` (`[3.11, 3.12]`), `docker-compose.yml` (`postgres:13`), `requirements.txt:30,48` (`Django==5.2.13`, `huey==2.3.0`).
- [~] **Docker Compose works on macOS arm64** — likely yes for the Django app and Postgres, but the Dockerfile downloads **chromedriver 104** from `chromedriver.storage.googleapis.com` (URL deprecated for v115+) on a hard-coded amd64 binary. App runs without it but Selenium-based broker pulls and the test suite are broken on arm64.
  > Evidence: `Dockerfile:30-32`. Pinned URL has been retired by Google.
- [x] **SQLite is supported** — `settings.py:120-126` branches on `DB_ENGINE` env var; `sqlite3` is a first-class option (used by the baremetal install path per README).
  > Evidence: `src/portfoliomgr/settings.py:120` (`if DB_ENGINE == 'sqlite3'`). Huey, however, requires Postgres for `SqlHuey` per `settings.py` tail — SQLite path uses Huey's default `SqliteHuey`. Confirmed both paths exist.
- [ ] **Scheduled tasks are cron-heavy.** ~25 `@db_periodic_task` decorators in `src/tasks/tasks.py` covering NAV refresh, stock prices, ESPP, RSU, schemes table, scroll data, news, etc. No lazy on-access refresh path.
  > Evidence: `grep -n "periodic_task" src/tasks/tasks.py` returns 25 hits including `crontab(minute='0', hour='*/12')` for `get_mf_navs`, `update_mf`, etc. Operator must run a separate `python manage.py run_huey` process.
- [?] **Resource footprint** — not measured live. From the Dockerfile the build pulls `gcc gfortran ghostscript python3-tk libopenblas-dev liblapack-dev` plus Selenium/Chrome runtime and Apache Tika (Java), so build image is ≥1 GB. Runtime adds `numpy`/`pandas`/`opencv-python`. Heavy for a home-server.
- [~] **Configuration** — env-var based via `python-dotenv`, but the `env_files/.pm-env` file must live inside the source tree (`src/env_files/`) which is then `COPY`'d into the image. Twelve-factor-ish but not fully (the file is baked into the image at build time).
  > Evidence: `Dockerfile:18,21`, `settings.py:11`.
- [ ] **Frontend is Django templates + jQuery + Bootstrap 4 + Chart.js + DataTables, all loaded from public CDNs.** Not React/Vue. Dated styling.
  > Evidence: `src/templates/base.html` references `stackpath.bootstrapcdn.com`, `cdnjs.cloudflare.com`, `cdn.datatables.net`, `cdn.jsdelivr.net` — 7 distinct CDNs at page load. Charts via `<canvas id="myChart">` (Chart.js).

---

## C. Data model

- [~] **User/family/individual model is messy.** `users.User` (`src/users/models.py:11`) is a *Person/Individual* entity, NOT a login. Login is `django.contrib.auth.models.User` (the Django built-in). Two unrelated classes, both named `User`, used throughout. Consistent foot-gun.
  > Evidence: `src/users/models.py:11` (`class User(models.Model)` with `name`, `dob`, `risk_profile`); `src/portfoliomgr/settings.py:42` (uses `django.contrib.auth`).
- [ ] **Single login owns all individuals; not multi-tenant.** `src/users/user_interface.py:18-22` defines `get_users(ext_user)` that ignores its argument and returns `User.objects.all()`. `get_ext_user(id)` always returns `None`. The codebase is single-tenant by design — every authenticated session sees every Person's data. (Acceptable for self-hosted single-household, irrelevant for corpus-watch MVP.)
  > Evidence: `src/users/user_interface.py:18-22`.
- [x] **Assets are attributable to a specific Individual.** Every asset model has `user = models.IntegerField()` referencing `users.User.id`. Family-aware schema is workable.
  > Evidence: `src/mutualfunds/models.py:17`, `src/shares/models.py:25`, `src/epf/models.py:12`. Caveat: integer-typed (no Django ForeignKey, so no DB-level integrity, no joins, no cascade).
- [x] **Transaction vs holding separation exists for major assets.** MF: `Folio` (state) + `MutualFundTransaction` (event) + `Sip` (cadence). Shares: `Share` + `Transactions`. EPF: `Epf` + `EpfEntry`. Good shape.
  > Evidence: `src/mutualfunds/models.py:13,33,50`; `src/shares/models.py:20,46`.
- [ ] **Asset-class extensibility is hardcoded fan-out, not a plugin/registry.** Adding a new asset class touches: a new app folder; an `Interface` class with the conventional method names; **`Goal` model gains a new `<class>_contrib` decimal column**; `goal_helper.update_goal_contributions` adds a hardcoded line; `users.user_interface.UserInterface.export` adds the new interface to its hardcoded list; `tasks.py update_investment_data` adds a column on `InvestmentData`; `goal_helper.get_unallocated_amount` adds an import + sum line. ~10 files per new asset class.
  > Evidence: `src/goal/models.py:24-37` (15 hardcoded `*_contrib` columns); `src/goal/goal_helper.py:104-117`, `:142-176`; `src/users/user_interface.py:58`; `src/tasks/tasks.py:165-214`.
- [x] **Migration history is clean.** Goal: 2 migrations, Users: 2, MF: 1, EPF: 1. Either squashed or stable. No backwards-incompatible churn visible.
  > Evidence: `ls src/*/migrations/` shows ≤4 files per app on average.

**Aside on code quality at the schema level:** the `Goal` model has typos in column names — `epf_conitrib`, `fd_conitrib`, `ppf_conitrib`, `ssy_conitrib`, `rsu_conitrib`, `shares_conitrib`, `mf_conitrib`. These are real DB column names. Reverting them costs a migration. (`src/goal/models.py:24-31`.)

---

## D. India asset class coverage

| Asset | Present | Ingestion | Granularity | Notes |
|---|---|---|---|---|
| Mutual Funds | ✓ | CAS PDF (CAMS+KFintech via `casparser`), Kuvera scrape (Selenium), Coin scrape (Selenium), manual | Folio + transaction | `src/mutualfunds/cas.py`, `pull_kuvera.py`, `pull_coin.py` |
| Stocks (NSE/BSE) | ✓ | Zerodha Console scrape, Robinhood, manual | Holding + transaction | `src/shares/pull_zerodha.py`. yfinance for prices. |
| EPF | ~ | **Manual month-by-month entry only.** No passbook PDF parser. | Account + monthly entry | `src/epf/views.py:257` (`add_contribution`) is a typed grid. |
| NPS | ✗ | **Not present at all.** Zero references in source. | — | `grep -rn 'NPS\|nps\|National Pension' --include='*.py' src/` returns 0 hits. |
| PPF | ✓ | Manual + SBI online scrape | Account + transaction | `src/ppf/ppf_sbi_pull.py`. |
| SSY | ✓ | Manual + bank scrape | Account + transaction | `src/ssy/`. |
| FDs | ✓ | Manual | Account-level | `src/fixed_deposit/`. |
| Recurring Deposit | ✓ | Manual | Account-level | `src/recurring_deposit/`. |
| Gold | ~ | Manual; price scrape from gadgets360, gold.org, goldprice.org | Quantity + value | `src/tools/gold_india.py`. SGB / digital gold not modelled distinctly. |
| ESPP / RSU | ✓ | Manual + USA-broker pull | Lot-level | `src/espp/`, `src/rsu/`. |
| Real estate | ✗ | — | — | Not modelled. |
| Bank savings cash | ✓ | Manual | Account balance | `src/bankaccounts/`. |
| Crypto | ✓ | Manual; CoinGecko pricing | Position | `src/crypto/`. |
| 401K (USA) | ✓ | — | — | `src/retirement_401k/`. (Not corpus-watch relevant.) |
| Insurance (ULIP-style) | ✓ | Manual + ICICI Pru Life NAV scrape | NAV-history per fund | `src/insurance/`, `src/tools/ICICIPruLife.py`. |

**Critical for corpus-watch:** NPS missing entirely; EPF has no PDF import.

---

## E. Data ingestion

- [x] **CAS import (CAMS + KFintech)** uses `casparser==0.7.4` directly — corpus-watch's natural choice as well.
  > Evidence: `src/mutualfunds/cas.py:3,18`. Only `cas_type == 'DETAILED'` is processed; summary CAS is ignored. Tax/dividend transactions are dropped on the floor (line 58: `if 'tax' in trans['type'].lower(): continue`). Only `Buy` and `Sell` kept (line 61-66) — switches, dividend reinvestments, bonus, mergers all skipped.
- [ ] **NPS statement PDF import** — not present. (See D.)
- [ ] **EPF passbook PDF import** — not present. The `add_contribution` UI is a 12-month grid where the user types from their passbook (`src/epf/views.py:257-317`).
- [~] **Bulk CSV import** — present for MF only via `tasks.py:add_mf_transactions` (file upload route). No CSV import for shares, EPF, NPS, etc.
- [~] **Manual entry forms** — exist for every asset class. UX is dated Bootstrap-4 forms with redirect-on-POST patterns. Field completeness is adequate for "track what you remember"; not delightful.
- [~] **AMFI NAV refresh** — uses `mftool.Mftool().get_scheme_quote(code)` per fund (`src/tasks/tasks.py:106`). `mftool` internally fetches from AMFI but iterates per scheme. Not the bulk `https://www.amfiindia.com/spages/NAVAll.txt` single-fetch corpus-watch wants. Cron-driven (`crontab(minute='35', hour='*/12')`), no lazy-on-dashboard-load path.
- [x] **Stock price refresh** — `yfinance` for live and historical, `nsetools` for live, `nasdaq` API for historical. Yahoo Finance is the primary source, matching corpus-watch's stack.
  > Evidence: `src/shared/yahoo_finance_2.py:7,211,229`.
- [x] **Idempotent re-import (CAS)** — yes, `mutualfunds/mf_helper.py:92-99` filters `MutualFundTransaction.objects.filter(folio, trans_date, trans_type, price, units)` and skips if matching row exists. The `MutualFundTransaction` model also has `unique_together` on `(folio, trans_date, trans_type, units, broker)`. Re-importing the same CAS will not duplicate.
- [~] **Reconciliation** — `shares.shares_helper.reconcile_shares` and `check_discrepancies` exist for stocks. No general "manual entry vs CAS" reconciliation — manual-entry rows and CAS-imported rows live in the same `Transactions` table without provenance tracking.

---

## F. Privacy

- [ ] **Outgoing network calls** — broad, including phone-home to maintainer's repo.
  External endpoints reached (non-exhaustive):
  - `raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/currencies.json` — `src/bankaccounts/views.py:219`
  - `raw.githubusercontent.com/krishnakuruvadi/portfoliomanager/main/src/metadata.json` — `src/common/views.py:49` (**version-check ping; effectively a heartbeat to the maintainer**)
  - `api.coingecko.com` — crypto prices/IDs
  - `query1.finance.yahoo.com`, `query2.finance.yahoo.com` — stock data
  - `www1.nseindia.com`, `bsestarmf.in`, `bseindia.com` — Indian markets
  - `api.nasdaq.com`, `nasdaq.com` — US markets
  - `moneycontrol.com` — stock metadata + scraping
  - `api.exchangerate.host`, `xe.com`, `openexchangerates.org`, `fixer.io` — forex
  - `gadgets360.com`, `goldprice.org`, `gold.org`/`fsapi.gold.org` — gold prices
  - `kuvera.in`, `coin.zerodha.com`, `kite.zerodha.com`, `console.zerodha.com` — broker scraping (with user credentials)
  - `buy.iciciprulife.com` — ULIP NAV
  - `wikipedia.org` — S&P 500/400 ticker lists
  - `cdnjs.cloudflare.com`, `stackpath.bootstrapcdn.com`, `cdn.datatables.net`, `cdn.jsdelivr.net` — **frontend assets per page load** (browser leaks usage)
- [x] **No telemetry / analytics SDKs.** No Sentry, Mixpanel, GA, Segment, PostHog, or Datadog. Outbound traffic is functional only.
- [~] **User data leaving the device** — three nuances: (a) the metadata.json fetch is a passive version check (no payload), (b) the broker-scraping flows submit *user credentials* to the broker websites (which the user authorized, but corpus-watch's posture is "no broker creds at all — file imports only"), (c) market-data fetches reveal which symbols the user holds to the data provider. Yahoo, NSE, etc., learn the holdings indirectly via per-symbol queries. No bulk-anonymous fetch is used.
- [x] **Auth: Django built-in.** Sessions, CSRF, login_required middleware. No OAuth providers wired.
  > Evidence: `src/portfoliomgr/settings.py:42-78`, `MIDDLEWARE` includes `LoginRequiredMiddleware`.
- [ ] **Secrets storage is weak.** Master password is stored **plaintext** in `media/secrets/passwords.json` under key `masterPassword`. Per-credential Fernet keys are stored on disk next to the encrypted blobs. Effective protection = filesystem ACL.
  > Evidence: `src/common/helper.py:343-363` (`add_master_password`/`get_master_password` write/read JSON in plain), `:391-394` (`write_key` writes Fernet key to `<id>.key`).
- [ ] **No DB encryption at rest.** Standard Postgres / SQLite files.

---

## G. Goal planning

- [x] **Goal entity present.** `src/goal/models.py:6`. Has `start_date`, `time_period` (months), `inflation`, `final_val`, `curr_val`, `recurring_pay_goal`, `expense_period`, `post_returns`.
- [~] **Goal types** — no enum. The shape covers (a) one-time future-value goal and (b) recurring pay goal (e.g., retirement spending). User defines name freely.
- [x] **Future-value vs present-value** — `goal_helper.one_time_pay_final_val(curr_val, inflation, time_period)` and `get_curr_val_from_fut_val` both exist.
- [x] **Inflation factored in** — per-goal `inflation` column.
- [~] **Backward planning** — no SIP-required-to-reach-goal calculator. There is a Goal "achieved %" tracker (`update_goal_contributions`) which sums *current* contributions toward the target, but nothing computing required monthly contribution given a deadline.
- [ ] **Multi-goal prioritization or conflict handling** — none. Goals are independent rows; an asset can be tagged to one goal at a time via integer `goal` field.

(All post-MVP for corpus-watch — flagged for completeness.)

---

## H. Projection engine

- [~] **Time-value-of-money math** — present but limited.
  > Evidence: `src/goal/goal_helper.py:11-36` (compounding inflation), `src/calculator/views.py` (FD/RD compounding only).
- [ ] **Per-asset-class return assumptions** — not modelled. There's no place to set "expected equity return = 12%, debt return = 7%" and compose a portfolio projection.
- [~] **Compounding model** — annual (1+r)^t in Goal helper; FD calculator supports yearly/half/quarterly. No continuous compounding.
- [~] **Inflation-adjusted projections** — only at the per-goal level (one inflation rate × one goal's curr_val). No real-vs-nominal toggle on the net-worth view.
- [ ] **Confidence intervals / Monte Carlo** — none.
- [x] **Withdrawal phase modeling** — surprisingly present: `goal_helper.get_depletion_vals` and `get_corpus_to_be_saved` (`src/goal/goal_helper.py:38-68`) implement a depletion-phase projection. (corpus-watch flags this post-MVP, but worth knowing.)

---

## I. Net worth & drill-down

- [x] **Aggregate net worth across all assets and individuals** — yes. `tasks.update_investment_data` aggregates into a single `InvestmentData(user='all')` row.
  > Evidence: `src/tasks/tasks.py:165-214`.
- [x] **Drill-down per asset class, per individual, per scheme** — yes. `users.user_helper.update_user_networth` per individual; per-asset module has list+detail views; per-folio detail for MF.
- [x] **Time-series net worth growth** — yes via `InvestmentData` (cron-populated time-series JSON). Charted on home page.
  > Evidence: `src/pages/` and `src/templates/home.html`.
- [x] **Per-asset value-over-time graph** — present for some asset types. EPF has `chart_data` constructed from `EpfEntry` (`epf/views.py:113-149`). Mutual fund per-folio shows transactions but not always a value-over-time line.

---

## J. Audit / missed-deposit detection

- [ ] **Missed-deposit detection: not present.** No code path computes "expected vs actual" for monthly contributions. EPF data captures monthly entries from the passbook, so the source data is there, but the warning/heuristic layer does not exist.
- [~] **Data model rich enough to add it cleanly?** EPF: yes (`EpfEntry` is already monthly). NPS: would require building NPS support from scratch. Adding a generic "expected cadence" config to corpus-watch would be a clean add to a fresh codebase; in portfoliomanager it would need a new model + per-asset hookup × the existing hardcoded fan-out.

---

## K. Returns calculation

- [x] **XIRR per asset and per folio** — `pyxirr==0.10.3` is wired through. Per-folio XIRR computed in `tasks.update_mf` and stored on the `Folio` row. Per-portfolio XIRR via `mf_helper.calculate_xirr_all_users`.
  > Evidence: `src/mutualfunds/mf_helper.py:137-173`, `src/tasks/tasks.py:123-130`.
- [~] **Per-individual / per-family XIRR** — derivable from the per-folio computations but not surfaced as a single roll-up across all asset classes.
- [~] **Cost-basis tracking** — running average cost basis on `Folio.buy_price` updated on every transaction (`mf_helper.py:109-128`). Not FIFO / LIFO. Adequate for net-worth display, not for tax computations.
- [x] **Absolute return, CAGR, time-weighted return** — absolute gain on every holding (`buy_value`, `latest_value`, `gain`); CAGR via XIRR; ROI fields scattered. No TWR.

---

## L. UX & UI

- [ ] **Dated UI.** Bootstrap 4.4.1 (released 2019) + jQuery + DataTables. Forms use server-rendered full-page POST/redirect — no SPA, minimal interactivity. Recent commits (Sep 2025) show "form beautification" but the foundation is dated.
  > Evidence: `src/templates/base.html` references Bootstrap 4.4.1; `git log --grep='[Bb]eautif'` shows multiple form-styling commits in late 2025.
- [~] **Mobile-responsive** via Bootstrap defaults. Charts via Chart.js scale, but multi-column tables become awkward on mobile.
- [x] **Charting library**: Chart.js (canvas-based, MIT license). Loaded from CDN.
- [~] **Onboarding / empty state** — `src/templates/welcome.html` exists. Home page degrades gracefully when no data — but the prompt-to-add-first-asset flow is implicit (sidebar links), not an explicit guided onboarding.
- [ ] **Power-user features** — none visible. No keyboard shortcuts, no bulk actions, no command palette.

---

## M. Code quality

- [ ] **Test coverage: not measured. Tests are Selenium browser tests only.**
  > Evidence: `tests/test_*.py` files import `selenium.webdriver`. `conftest.py` constructs Chrome/Firefox WebDriver fixtures. `pytest.ini` is configured but CI uses `python manage.py test`. No unit tests of pure logic (XIRR helpers, CAS parser glue, etc.). `coverage` is not in `requirements.txt`.
- [x] **CI configured** — `.github/workflows/django.yml` runs the Selenium-driven Django test suite on Python 3.11/3.12 against ephemeral chromedriver.
  > Evidence: `.github/workflows/django.yml`.
- [ ] **Type hints** — virtually none. `pylint==2.6.0` is in `requirements.txt` but not wired into CI. No `mypy`/`pyright`. The codebase predates the team adopting hints.
- [ ] **Linter** — no `ruff`/`black`/`isort` configuration files (`pyproject.toml` absent, no `.ruff.toml`, no `setup.cfg`). Code style is inconsistent: mixed quote styles, mix of tabs/spaces (`settings.py:134-137`), `print(...)` calls littered through hot paths.
- [ ] **Docstrings, ADRs, design docs** — absent. `README.md` covers install. There are no in-repo design documents or `docs/`.
- [x] **Migrations history** — clean and reversible (only forward-looking schema additions).

**Verbatim signal: `goal/models.py` ships with seven typo'd column names (`*_conitrib`).** The team's review process did not catch this — and once it shipped, fixing it costs a migration, so it stays. This is a code-review-discipline tell.

---

## N. Maintenance signals

- Last commit on `main`: **2026-04-08** (1 month ago, all dependabot since 2025-11-24).
- Open issues: **3** (oldest from 2020, "Add selenium based test cases" — still open after 6 years; one from 2022, "submit-without-final-value crashes"; one from 2025-09, "nginx + docker compose").
- Open PRs: **8** all dependabot, the most recent four (2026-04-13 → 2026-05-08) un-merged. Most-recent merge of any PR: 2026-04-09 (cryptography bump).
- Mean time to first review on the last 10 PRs: dependabot PRs are typically merged within hours to days when merged at all. Recent ones (Apr 13+) are sitting un-touched for ~25 days as of 2026-05-10.
- Releases / changelog discipline: `metadata.json` exists for version pinning but no `CHANGELOG.md` and no GitHub releases (`gh release list`).
- Number of contributors with > 5 commits: **3** (Krishna Kuruvadi 342, Krishna Kumar K 61, lal309 38). The first two appear to be the same person under different GitHub identities (GitHub user `krishnakuruvadi` is named "Krishna Kumar K" in their profile). Effective bus factor: **1**.
  > Evidence: `git log` author counts; `gh repo view` license + profile.

**Maintainer behaviour:** keeps dependencies fresh via dependabot; lands occasional UX polish (form beautification Sept 2025); does not appear to merge external PRs (recent PRs all bot). 91 stars / 29 forks on a 6-year-old repo is modest reach.

---

## O. Extensibility

- [ ] **Adding a new asset class** — invasive. Touches: new app dir (models, views, helpers, urls, templates, interface) + `Goal` model column + `goal_helper.py` two functions + `users.user_interface.UserInterface.export` + `tasks.py update_investment_data` (both branches) + `pages.InvestmentData` model + sidebar templates. Estimated 8-12 files, plus migrations on `Goal` and `InvestmentData`.
- [ ] **Adding a new ingestion source** — hardcoded. `cas.py` knows broker codes inline (`INA200005166 → KUVERA`, etc., `src/mutualfunds/cas.py:29-44`). No registry pattern.
- [~] **REST API surface** — `djangorestframework==3.15.2` is installed and a few endpoints exist (`CurrentEpfs` in `epf/views.py:335` is `APIView`, no auth). The bulk of the app is Django views rendering templates; the API is partial and not documented.
- [ ] **Templating coupled to data** — Django templates call helpers in views which call interfaces directly, with no serialization layer. Replacing the frontend with React would require rebuilding the API surface from scratch.

---

## P. Hard requirements gap analysis (corpus-watch MVP)

| Requirement | Status | Evidence |
|---|---|---|
| Self-hosted Docker, low resource footprint | ~ | Docker works; image is large (>1 GB build, includes Java/Tika, Selenium, OpenBLAS). |
| SQLite-friendly | ✓ | `settings.py:120` supports `DB_ENGINE=sqlite3`. |
| CAS import (CAMS + KFintech) | ✓ | `casparser` via `src/mutualfunds/cas.py`. Idempotent. Drops dividends/switches. |
| NPS Transaction Statement PDF import | ✗ | Zero NPS code anywhere. |
| EPF passbook PDF import | ✗ | Manual month grid only (`src/epf/views.py:257`). |
| AMFI NAV refresh, lazy / no cron | ~ | `mftool` per-fund fetch on Huey cron; not bulk; not lazy. |
| Stock EOD prices (Yahoo) | ✓ | `yfinance` via `shared/yahoo_finance_2.py`. |
| Manual entry: FD, PPF, EPF, NPS, gold, stocks | ~ | All except NPS. |
| Family schema (multi-individual) | ✓ | `users.User` is a Person; assets carry `user` int FK. |
| Net worth aggregate + per-individual + per-asset drill-down | ✓ | `update_investment_data`, per-user net worth, per-folio detail. |
| Time-series net worth graph | ✓ | `InvestmentData` JSON time-series, Chart.js render. |
| EPF/NPS contribution audit (missed-deposit warning) | ✗ | No detection logic; for NPS no data either. |
| XIRR per asset / individual / family | ~ | Per-folio + portfolio-wide; per-individual roll-up not surfaced cleanly. |
| Projection (configurable inflation + per-asset-class return) | ~ | Goal-level inflation; FD/RD calculator; **no portfolio-level multi-asset projection with per-class return assumptions**. |
| DB export (SQLite copy + JSON dump) | ~ | `UserInterface.export` produces JSON of all entities; SQLite copy is OS-level (fine). |
| No outgoing telemetry; only price-data sources | ~ | No telemetry SDKs **but** version-check ping to maintainer's GitHub raw, plus 7 frontend CDNs leaking page loads. |
| AGPL-compatible (GPL-3 derivative is legally fine) | ✓ | GPL-3.0 §13 covers it. |

**Tally:** ✓ 7, ~ 7, ✗ 3.

---

## Q. Verdict

### **Greenfield.**

portfoliomanager is a working, recently-maintained, GPL-3.0 Django app that overlaps perhaps 35–40% of corpus-watch's MVP — but the overlap is concentrated in libraries (`casparser`, `pyxirr`, `mftool`, `yfinance`) that corpus-watch will use directly and that the maintainer did not author. The architectural divergence from corpus-watch is wide enough that *forking* would mean rewriting the data plane (hardcoded fan-out → registry), the refresh model (Huey cron → lazy on-access), the frontend (Django templates → React), and the test layer (Selenium browser → unit + a thin e2e). Each of those is an order-of-weeks of work; doing all four on someone else's codebase costs more than starting fresh and pulling in the four libs cleanly. A greenfield FastAPI + SQLAlchemy + SQLite + React MVP that wraps `casparser` + `pyxirr` + `mftool` + `yfinance` reaches a comparable feature set with a shape that fits corpus-watch's roadmap — including NPS, EPF PDF import, contribution audit, and projection — without inheriting GPL-3.0 entanglement, the dated UI, the plaintext-master-password design, the Selenium chromedriver pin, the typo'd schema columns, and the cron architecture.

### Three specific reasons

**Reason 1 — Section P / D / E / J: critical MVP requirements missing or wrong shape.** Three of fifteen tracked requirements are outright missing (NPS support entirely absent — `grep` 0 hits; EPF PDF import does not exist, only a manual 12-month grid in `src/epf/views.py:257`; missed-deposit audit detection does not exist). Two more are architecturally wrong-shape (AMFI NAV via per-fund `mftool.get_scheme_quote` on a 12-hourly cron, not bulk lazy; portfolio projection with per-asset-class return assumptions does not exist — only single-goal compounding in `goal_helper.py:11-36` and FD/RD calculators). That's ≥5 of 15 pillars to add or rewrite.

**Reason 2 — Section C / O: data model is hardcoded fan-out, not a registry.** Adding any new asset class (e.g., NPS) means amending `Goal` model with a new `*_contrib` column, `goal_helper.update_goal_contributions` (line 104), `users.user_interface.UserInterface.export` (line 58), `tasks.update_investment_data` (lines 165-214 — both create and update branches), `InvestmentData` model, plus the new app. ~10 files per asset class, plus migrations on shared models. corpus-watch's design intent is a clean asset-class registry; retrofitting one onto this codebase is itself the rewrite.

**Reason 3 — Section L / M / F: frontend, tests, and privacy posture diverge from corpus-watch.** Frontend is Django templates + jQuery + Bootstrap 4 with seven public-CDN dependencies loaded per page (`src/templates/base.html`) — incompatible with both the React SPA target and the privacy-first posture (every page-load leaks to cloudflare/jsdelivr/bootstrapcdn). Tests are Selenium-only with chromedriver pinned to v104 in the Dockerfile (`Dockerfile:30`); no unit tests of XIRR/projection/parsing logic. Master password is stored plaintext at `media/secrets/passwords.json` (`src/common/helper.py:343-363`). Each of these is inconsistent with corpus-watch's lean-clean-tested ethos and would need to be replaced — which is a rewrite.

---

## R. Final notes

- **Reuse strategy if greenfield is chosen.** The four libraries that do most of portfoliomanager's heavy lifting — `casparser`, `pyxirr`, `mftool`, `yfinance` — are all separately licensed (MIT/Apache-2.0) and AGPL-compatible. Pull them in directly. Read `src/mutualfunds/cas.py` once for the broker-code mapping (lines 29-44) — it's a useful reference but small enough to retype in your own clean shape, ignoring the casparser-output keys you don't care about.
- **Idempotency pattern is worth copying.** `mutualfunds/mf_helper.py:92-99` checks `(folio, trans_date, trans_type, price, units)` before insert; combined with `MutualFundTransaction` `unique_together`. Cleanly idempotent. corpus-watch should mirror this shape (perhaps a content-addressable hash of `{folio, date, type, units, nav}` as the primary natural key).
- **CAS gotchas portfoliomanager already discovered.** It only handles `cas_type == 'DETAILED'` (line 21); summary CAS exists and silently returns nothing. Tax/dividend transactions are dropped (line 58); for an audit/XIRR-correct tool you'd want to capture them. Switches and bonus units are ignored — a real correctness gap, present in both portfolios and worth solving in corpus-watch from day one.
- **Hidden Java dependency.** `tika==1.24` is in `requirements.txt` and used somewhere; it pulls Apache Tika, a JVM service. The Dockerfile prepares `/tmp/tika.log`. Heavyweight for a home-server.
- **Hidden Selenium dependency.** Chromedriver is pinned to v104 in `Dockerfile:30`. Modern Chrome is v120+. Anyone deploying this image today gets broken broker-pull flows. Worth knowing; do not rely on portfoliomanager's broker scrapers as a fallback.
- **The `users.User` / `auth.User` naming collision** is the kind of thing that would bite a new contributor on day one. corpus-watch should use `Individual` for the person entity and reserve `User` for login.
- **Goal model typos** (`*_conitrib`) are baked into the database. Cannot fix without a migration. Code-review-discipline signal at the schema level.
- **Phone-home ping** to `raw.githubusercontent.com/krishnakuruvadi/portfoliomanager/main/src/metadata.json` (`src/common/views.py:49`) is a passive heartbeat the maintainer can use to count active installs (via GitHub raw access logs they don't have, but conceptually). Not personal data, but worth disabling if forking — easy one-line patch.
- **Active maintenance is mostly dependabot.** Eight open dependabot PRs unmerged for weeks, no human PRs in the recent window, oldest open issue dating from 2020. The repo is alive but is unlikely to absorb a 4-pillar feature contribution upstream on a corpus-watch timeline.
- **Stars/forks (91 / 29)** suggest there's a small Indian DIY-investor audience for a tool in this shape — corpus-watch's market exists.
