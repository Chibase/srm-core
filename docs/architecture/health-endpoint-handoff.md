## Constraints / Risks / Assumptions (handoff)

### Constraints
- Minimal change only.
- No auth changes.
- No deep DB health checks.
- No observability integration.
- No breaking route changes.

### Assumptions
- Deployed site uses standard Frappe website routing so `www/health.py` maps to `/health`.
- Load balancers can access the Frappe site origin for `/health` (not desk-only).

### Risks / Unknowns
- JSON response behavior for `www` routes can vary by Frappe version; verify endpoint returns raw JSON (not HTML wrapper) on target bench.
- If production enforces login or blocks website routes, guest `/health` may require infra exception.
- Issue says “API”, but `apps/api` is empty; implementing there may not ship.

### Definition of Done
- Acceptance criteria satisfied.
- CI green.
- Reviewer approval obtained.
- Docs updated if needed.
- Rollback path included in PR.
