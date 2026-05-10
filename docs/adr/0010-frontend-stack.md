# ADR-0010: Frontend stack — React + Vite + TypeScript bundle

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch's frontend is a single-page application served by the FastAPI backend (see [ADR-0005](0005-backend-stack.md)). It runs in a browser on the LAN, authenticated by deployment context (no auth in MVP per [ADR-0007](0007-self-hosted-single-tenant.md)). It does not require SEO, server-side rendering, or static-site generation.

The frontend will render a data-heavy dashboard: net worth aggregations, time-series charts, drill-downs by individual, asset class, and asset. Data comes from the backend over HTTP/JSON; no third-party data fetching from the browser (privacy posture, see [ADR-0002](0002-frontend-asset-loading.md)).

## Build tool — options considered

1. **Vite** — Rollup + esbuild. Fast dev (sub-second HMR). Official React docs recommend it (Create React App is deprecated). Outputs static assets; no Node runtime in production.
2. **Next.js** — React framework with SSR/SSG/Server Components. Heavier; requires a Node runtime. SEO and SSR not needed for our use case.
3. **Remix / React Router 7** — full-stack framework with loader/action pattern. Tied to a backend-conventions model we don't use.
4. **TanStack Start** — newer (2025), file-based routing, type-safe loaders. Smaller ecosystem; risk for a solo dev who values boring choices.
5. **Bun bundler** — fast, ESM-first. Smaller ecosystem; less battle-tested for production deploy.
6. **Webpack / Parcel** — outdated for new projects.

## Decision — full bundle

**React 18+ with TypeScript (strict, `noImplicitAny`, no explicit `any`). Built with Vite.**

| Concern | Choice |
|---|---|
| Build tool | **Vite 7+** |
| Language | **TypeScript** in strict mode |
| Routing | **React Router** (v7+) |
| Server state | **TanStack Query** (React Query) |
| Global client state | **React Context** + `useState` (no library in MVP) |
| Styling | **Tailwind CSS** |
| Forms | **React Hook Form** |
| Charts | **Recharts** |
| Tests | **Vitest** + **React Testing Library** |
| Linting | **ESLint** + **typescript-eslint** |

### Reasons — build tool

- **Vite outputs static assets.** FastAPI (or nginx in front) serves them. Zero Node runtime in production. Self-hosted users get one container, not two.
- **Fastest dev loop.** esbuild + HMR; sub-second iteration matters for a solo dev.
- **Vitest pairs natively.** Same config as Vite, no separate transform pipeline.
- **Boring + standard.** React docs recommend it. Large plugin ecosystem. Well-documented for a future contributor.

### Reasons — bundle elements

- **TypeScript strict.** `tsconfig.json` `"strict": true` (turns on `noImplicitAny`, `strictNullChecks`, `noUncheckedIndexedAccess` recommended). ESLint `@typescript-eslint/no-explicit-any: "error"` blocks explicit `any`. Enforced in CI via `tsc --noEmit`.
- **TanStack Query for server state.** Caches, refetches on focus, deduplicates in-flight requests, supports optimistic updates. Replaces hand-rolled fetch/caching. Essential for a data-heavy dashboard.
- **React Context + `useState` for global client state.** corpus-watch's global client state is small (selected individual context, theme, filter selections). Three slices do not justify a state-management library. If pain emerges (Context re-renders or store growth), revisit with Zustand.
- **Tailwind CSS.** Removes per-component CSS decision fatigue. No CSS-in-JS runtime cost. Compiled output is small. Pairs cleanly with shadcn/ui or vanilla components.
- **React Hook Form.** Performant (uncontrolled inputs by default), TypeScript-friendly, mature.
- **Recharts.** Declarative React charts; sufficient for our line, bar, pie, and area chart needs. Mature; widely used.
- **Vitest + React Testing Library.** Vite-native test runner, jest-compatible API. RTL pushes test design toward user-visible behaviour.

## Consequences

### Accepted

- ESM-first ecosystem. Rare CommonJS-only packages may need workarounds; uncommon in 2026.
- TypeScript strict requires up-front type effort. Pays off in refactor confidence and CI safety.
- Migration to SSR (Next.js, Remix) is a rewrite of routing and data fetching. Out of scope for our self-hosted SPA.

### Enabled

- Static asset deployment: FastAPI serves the built `dist/` directly. One container.
- Type-safe end-to-end: backend OpenAPI → generated TS client → React components.
- Standard React stack: any future contributor onboards via React + Vite docs.
- Modern test ergonomics: Vitest hot-reloads with the dev server.

### Foreclosed

- SSR / SSG. Not pursued.
- App-store native frontend. Browser-only.

## References

- [Vite](https://vitejs.dev/)
- [TanStack Query](https://tanstack.com/query)
- [React Hook Form](https://react-hook-form.com/)
- [Recharts](https://recharts.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vitest](https://vitest.dev/)
- [ADR-0002 — Frontend asset loading policy](0002-frontend-asset-loading.md)
- [ADR-0005 — Backend stack](0005-backend-stack.md)
- [ADR-0007 — Self-hosted, single-tenant deployment](0007-self-hosted-single-tenant.md)
