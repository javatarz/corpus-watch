# ADR-0002: Frontend asset loading policy

- **Status**: Accepted
- **Date**: 2026-05-10

## Context

corpus-watch is a privacy-focused, self-hosted net worth tracker. The frontend is a React SPA bundled with Vite. The initial CLAUDE.md draft included a hard "no CDN" rule, framed as a privacy concern. On reflection, the threat model is narrower than the rule assumed: the user cares about confidentiality of financial data (assets, liabilities, balances), not about hiding the fact that they use the tool.

This recalibration changes which risks matter:

- **Fingerprinting** (CDN provider learns "this IP uses corpus-watch") — out of scope.
- **Data confidentiality** (third party learns balances/holdings) — in scope; must defend.
- **Supply-chain attack** (CDN serves compromised JS, malicious code reads DOM with rendered balances and exfiltrates) — in scope; must defend.

Bundling everything defends all three risks, but at the cost of foreclosing CDN conveniences (e.g. font CDNs with broad glyph coverage, fonts/icons not in `node_modules`). For a data-confidentiality-only threat model, a blanket bundle rule is over-tight.

## Options considered

1. **No CDN at all.** Bundle everything. Defends all three risks. Forecloses font CDN convenience. Simple rule, hard to violate accidentally.
2. **CDN with version-lock only.** Pinning protects against silent major-version bumps but not against compromise of the pinned version itself (e.g., Polyfill.io 2024 served malicious code from a versioned URL). Insufficient.
3. **CDN with version-lock + Subresource Integrity (SRI).** SRI = browser computes hash of fetched asset, refuses to execute on mismatch. Supply-chain compromise of the served file is blocked. Financial-data confidentiality preserved (CDN sees IP and Referer, not balances).
4. **Unrestricted CDN.** No discipline; library JS can be hijacked, balances exfiltrated. Rejected.

## Decision

**Option 3.** Bundle preferred for code; CDN allowed under three mandatory conditions:

1. Version-locked (exact semver, no floats, no `latest`).
2. Subresource Integrity attribute on every `<script>` and `<link>` tag (`integrity="sha384-..."`).
3. CDN provider on an approved list (jsdelivr, cdnjs, unpkg). New providers added via PR.

Bundling is the default because Vite makes it zero-cost (libraries are already in `node_modules`), removes the CDN-downtime failure mode, and yields a simpler audit trail. CDN is reserved for cases where it solves a real problem (fonts, icons with broader glyph coverage than self-hosting offers), not for libraries already installable.

## Consequences

### Accepted

- Reviewers must verify SRI on any CDN tag in PR review. Catchable by a lint rule or CSP `require-sri-for` directive.
- Slightly more nuanced rule than a flat ban. Cost accepted for the convenience of font CDNs et al.

### Enabled

- Font CDN usage with broad glyph coverage (Devanagari, Tamil, etc. for the Indian audience) without bundling weight.
- SRI-protected against supply-chain compromise.
- Future relaxation possible (e.g., growing the approved-provider list) without rewriting the rule.

### Foreclosed

- "Just drop a `<script>` tag" workflow. Every CDN inclusion requires generating an SRI hash.

## References

- [CLAUDE.md § Frontend asset loading](../../CLAUDE.md)
- [W3C Subresource Integrity specification](https://www.w3.org/TR/SRI/)
- Polyfill.io 2024 supply-chain incident — illustrative case for SRI necessity
