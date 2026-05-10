# ADR-0007: Self-hosted, single-tenant deployment

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch's primary product principle is "privacy is the product" ([VISION.md](../VISION.md)). User financial data must never traverse a network boundary the user does not control. That principle constrains deployment options sharply.

A second constraint comes from the family unit: a household has one or more individuals who should share a single view of their combined wealth. The deployment must accommodate multiple humans on the same network.

## Options considered

1. **Local desktop app (Tauri / Electron / native)** — maximum privacy; data lives on one machine. Hard to share across family devices without bespoke sync.
2. **Self-hosted server (Docker on home server / NAS / VPS)** — privacy preserved (user controls the host); naturally multi-device via LAN browser access; family-shareable.
3. **End-to-end encrypted cloud (vendor hosts, can't read)** — easiest UX, but adds vendor trust burden, key management complexity, and SaaS costs. Engineering bar high for a solo dev.
4. **Hybrid (local app with optional self-hosted sync)** — combines complexity of all three.

## Decision

**Self-hosted server, single-tenant per household. Docker Compose deployment. Browser-based UI accessible over LAN.**

### Reasons

- **Family unit naturally maps to one server.** A couple plus children share one network and one corpus-watch deployment. No multi-tenant complexity needed in MVP.
- **Browser-first.** Any device on the LAN (phone, laptop, tablet) accesses the same UI. No app install, no native build matrix.
- **Docker is mainstream for self-hosting.** Synology NAS, Raspberry Pi, Unraid, home Linux box — all run Docker Compose comfortably.
- **No SaaS hosting costs or vendor trust.** Aligns with "privacy is the product."
- **Simpler engineering.** No multi-tenant data isolation, no per-user auth in MVP, no key escrow. Solo dev can ship faster.
- **Future remote access is the user's concern.** Tailscale, port forwarding, reverse proxy — well-trodden paths. Not corpus-watch's problem to solve.

## Consequences

### Accepted

- **No auth in MVP.** Single-tenant home server, trusted LAN. Per-individual auth is post-MVP.
- **User responsible for backups.** Mitigated by the export feature (SQLite file copy + JSON dump per entity, see [SCOPE.md](../SCOPE.md)).
- **User responsible for updates.** `docker compose pull && docker compose up -d` is familiar to the target audience.
- **User responsible for remote access.** Documented in README post-MVP; not built in.
- **No multi-household tenancy.** A second household = a second deployment.

### Enabled

- Privacy: data never leaves the user's network unless they choose to expose it.
- Family-shareable from day one (LAN access).
- Cheap deployment: any home server hardware.
- Simple security model: trust the LAN, defer auth.

### Foreclosed

- SaaS hosting. Not pursued.
- Multi-tenant cloud product. Not pursued.
- App-store distribution (would conflict with self-hosted browser-based model).

## References

- [VISION.md](../VISION.md)
- [SCOPE.md](../SCOPE.md)
- [ADR-0006 — Database: SQLite](0006-database-sqlite.md)
