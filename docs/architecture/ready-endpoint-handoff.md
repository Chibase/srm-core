## Constraints / Risks / Assumptions (handoff) — GET `/ready`

### Constraints
- Minimal change only; mirror existing `/health` page-renderer pattern.
- No auth changes.
- No deep dependency diagnostics (no explain plans, no multi-key Redis scans, no external HTTP).
- No observability platform integration.
- No breaking route changes (`/health` and TrustLedger RPC unchanged).
- Checks must be fast and non-invasive (single ping/query each).

### Assumptions
- Site uses standard Frappe DB + Redis cache configuration (same as CI: MariaDB + redis-cache).
- `frappe.cache().ping()` (or equivalent on target Frappe version) is available for cache Redis.
- Orchestrators will treat HTTP `503` as not-ready and `200` as ready.
- Load balancers can reach website origin for `/ready` (same as `/health`).

### Risks / Unknowns
- Exact Redis ping API may differ slightly by Frappe version — Build must verify on target bench.
- If production blocks guest website routes, `/ready` needs the same infra exception as `/health`.
- Forcing Redis down in shared CI may be unsafe — prefer **mocked** not-ready tests over killing CI services.
- Returning structured `503` on check failure must not leak secrets in `detail`.

### Definition of Done
- Acceptance criteria satisfied (ready + not-ready paths).
- CI green.
- Reviewer approval obtained.
- Docs updated (`TRUSTLEDGER_API` Platform probes + README).
- Rollback path included in PR.

### AI Tool Assignment
- Spec: Gemini → `docs/architecture/ready-endpoint-spec.md`
- Build: Cursor
- Verify: GitHub Copilot
- Final sign-off: Human reviewer
