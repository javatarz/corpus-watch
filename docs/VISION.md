# Vision

## Problem

Indians struggle to financially plan their long-term wealth. Investments are fragmented across mutual funds (multiple AMCs), stocks (NSE/BSE), retirement vehicles (EPF, NPS, PPF, SSY), fixed deposits across banks, gold, and real estate. No two registrars share data. Aggregation requires manual spreadsheet labour or surrendering data to commercial aggregators that monetise it via ads and partner sales.

Existing tools fail along at least one of three axes:

1. **Privacy** — INDmoney, Smallcase, Groww, Kuvera et al. read your data and use it for advertising or upsell. The Account Aggregator framework is regulated to FIU NBFCs only; an individual cannot run it themselves.
2. **Family-aware** — most tools model individuals, not households. Spouses cannot share a unified view; goals like "₹1 Cr for child's education in 2042" cross individual ledgers.
3. **Configurability and projection** — projection assumptions are baked in or trivial. DIY investors who already understand SIP, XIRR, and indexation cannot tune the model to their reality.

## Audience

DIY Indian investor — household head who already manages investments via Zerodha, Coin, MFCentral, NPS portal, EPFO, etc. Comfortable downloading a CAS PDF. Wants one canonical view across the household, with privacy and projection tuning under their control.

**Not the audience:** financially passive users who want a robo-advisor; institutional or HNI users who need tax filing, estate planning, or compliance workflows.

## Principles

1. **Privacy is the product.** Self-hosted by default. No telemetry. No outgoing calls except to public price feeds (AMFI, Yahoo Finance EOD). User data never crosses a network boundary they don't own.
2. **Lean MVP, fast iteration.** Ship a usable v1 quickly; iterate. Reject features that don't earn their complexity.
3. **Family-first data model.** Schema treats individuals and households as first-class from day one, even if v1 UI shows one person.
4. **Configurability over defaults.** Inflation rate, return assumptions, asset-class membership — user-tunable. Defaults sensible, not opinionated.
5. **Reuse where possible.** Battle-tested libraries (`casparser`, `pyxirr`, `mftool`, `yfinance`) preferred over reinvention.
6. **Code as if maintainers are scarce.** Clean, type-hinted, well-tested. CI from day one. Boring stack.

## Non-goals

- Tax filing or tax optimisation (rules change too often; defer).
- Robo-advisory or any execution of trades/SIPs.
- SEBI- or RBI-regulated activities (advice, distribution, AA-FIU).
- Insurance gap analysis.
- Multi-currency (post-MVP).
- Mobile-native app (web-first, mobile-responsive).
- Multi-tenant SaaS hosting (single household per deployment).

## Success criteria for v1

A solo DIY investor can:

1. Spin up corpus-watch on a home server in under 15 minutes.
2. Upload one CAS PDF (CAMS or KFintech) and see all their MF + stock holdings.
3. Add NPS via statement PDF, EPF via passbook PDF, and FDs manually.
4. View aggregate net worth, drill down to a single scheme, see value-over-time.
5. Get a warning when a monthly EPF or NPS contribution didn't show up.
6. See a projection of their net worth at retirement, tunable by inflation and per-asset-class return.
7. Export their database as a SQLite file or JSON dump in one click.
