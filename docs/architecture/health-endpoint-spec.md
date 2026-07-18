# Spec: GET `/health` — Issue #2

**Issue:** https://github.com/Chibase/srm-core/issues/2  
**Title:** [AI Task] feat: add health check endpoint for API  
**Handoff companion:** `docs/architecture/health-endpoint-handoff.md`

**Repo reality:** SRM Core is a Frappe app (`srm_core/`). `apps/api/` is an empty scaffold. Product HTTP APIs today are `@frappe.whitelist()` methods under `srm_core.api.*` (RPC paths like `/api/method/...`). There is **no** existing health endpoint and **no** `www/` routes. Literal `GET /health` therefore needs a website page route (or infra rewrite), not only a whitelist method.

---

## 1) Endpoint Contract

| Item | Spec |
|------|------|
| Method / path | `GET /health` |
| Auth | Public / guest-allowed (no login, no CSRF token required for probes) |
| Success status | `200` |
| Content-Type | `application/json` |
| Caching | `Cache-Control: no-store` (or Frappe `no_cache = 1` equivalent). Must not be CDN/browser cached. |
| Side effects | None (no DB reads/writes, no auth mutations) |

**JSON body (exact fields):**

```json
{
  "status": "ok",
  "service": "srm-core",
  "timestamp": "2026-07-18T10:00:00+00:00"
}
```

| Field | Type | Rules |
|-------|------|--------|
| `status` | string | Always `"ok"` when the handler runs successfully |
| `service` | string | Always `"srm-core"` (literal; not `srm_core`) |
| `timestamp` | string | ISO-8601 datetime; generate at request time; prefer UTC with offset or `Z` |

**Non-goals for response:** version, DB latency, dependency checks, uptime counters.

---

## 2) Architecture Fit

### Where to register

| Layer | Path | Role |
|-------|------|------|
| Payload helper | `srm_core/api/health.py` | Pure function e.g. `build_health_payload()` returning the dict above; unit-testable without HTTP |
| Public route | `srm_core/www/health.py` | Frappe website page → **`GET /health`** (matches AC path) |
| Docs | `docs/TRUSTLEDGER_API.md` (+ optional one-line README note) | Document probe path separately from TrustLedger RPC methods |

**Do not** implement under empty `apps/api/`. That scaffold is not wired.

### Framework conventions to follow

- Frappe auto-exposes `www/<name>.py` as `/<name>` — use `www/health.py` for literal `/health`.
- Set `no_cache = 1` on the page module.
- Return JSON via Frappe response (`type: json`), not an HTML template.
- Keep handler guest-accessible (website page / guest-safe); **no** new roles or permission DocTypes.
- Optional (not required for AC): also `@frappe.whitelist(allow_guest=True)` wrapping the same payload for `/api/method/srm_core.api.health.health` — only if useful for internal RPC; **primary contract remains `GET /health`**.
- No `hooks.py` API registration needed for www pages; do not add `website_route_rules` unless required for a custom path (default `/health` is enough).

### Existing patterns to mirror

- API modules live under `srm_core/api/*.py` (see `auth.py`, `incidents.py`).
- Tests call Python functions directly (`FrappeTestCase`), see `srm_core/srm_core/tests/test_trustledger_api.py`.
- TrustLedger method inventory is in `docs/TRUSTLEDGER_API.md` — add a **Platform probes** subsection so `/health` is not confused with Packet 16 RPC methods.

---

## 3) Error / Edge Cases

| Case | Expected behavior |
|------|-------------------|
| App fully up, handler reached | `200` + JSON contract |
| App / worker still booting (process not accepting) | Reverse proxy / process manager returns connection error or `502`/`503` — **out of app control**; do not invent an in-app “booting” payload |
| Handler exception | Prefer fail loud (5xx) rather than returning `"ok"`; do not catch-and-mask |
| Timestamp consistency | One generation per request; always ISO-8601; document UTC preference; tests assert parseable ISO + presence, not exact clock value |
| Guest vs logged-in | Same response for both |
| Caching | Must not serve stale `"ok"` after process death (hence no-store / no_cache) |
| Backward compatibility | **None** — new route only; do not rename/move existing `/api/method/srm_core.api.*` paths |
| Deep health | Explicitly forbidden — no DB ping, Redis, queue checks |

---

## 4) Test Specification

**New file (recommended):** `srm_core/srm_core/tests/test_health.py`  
(Keep separate from TrustLedger suite to avoid fixture overhead.)

### Unit

| ID | Case | Assertions |
|----|------|------------|
| U1 | `build_health_payload()` shape | Keys exactly `status`, `service`, `timestamp` |
| U2 | Field values | `status == "ok"`, `service == "srm-core"` |
| U3 | Timestamp | Non-empty string; parseable as ISO-8601 datetime |

### Integration (HTTP or request simulation)

| ID | Case | Assertions |
|----|------|------------|
| I1 | `GET /health` as Guest | Status `200` |
| I2 | Response headers | Content-Type includes `application/json` |
| I3 | Body fields | Same as U1–U3 on parsed JSON |
| I4 | No auth required | Succeeds without login / without API key |

**CI:** Must pass under existing app test gate:

```bash
bench --site <SITE> run-tests --app srm_core --module srm_core.srm_core.tests.test_health
```

(Also ensure full `srm_core` suite / PR CI remains green.)

**Manual:** `curl -i https://<site>/health` → `200` + JSON fields.

---

## 5) Documentation Updates

| File | Change |
|------|--------|
| `docs/TRUSTLEDGER_API.md` | Add short **Platform probes** section documenting `GET /health` contract (not a TrustLedger RPC method) |
| `README.md` | Optional one-liner under ops/dev that `/health` is the liveness probe — only if README already lists endpoints; otherwise TRUSTLEDGER_API is enough |
| `docs/automation/*` | No change |
| Issue #2 | Link this spec + handoff for Build handoff |

---

## 6) Rollback Plan

1. Revert the merge commit / deploy previous `srm_core` revision (safe — additive route only).
2. Or delete `srm_core/www/health.py` (+ `srm_core/api/health.py` and tests) and redeploy.
3. No data migrations; no config flags; no auth/permission cleanup.
4. Monitors pointing at `/health` will fail open (probe fail) after revert — update or disable probes if needed.
5. Existing TrustLedger `/api/method/...` routes unaffected.

---

## 7) Execution Plan (Cursor checklist)

1. Add `srm_core/api/health.py` with `build_health_payload()` (and optional guest whitelist wrapper if desired).
2. Add `srm_core/www/health.py` exposing `GET /health` as JSON with `no_cache = 1`.
3. Add `srm_core/srm_core/tests/test_health.py` covering U1–U3 and I1–I4 as feasible in FrappeTestCase.
4. Update `docs/TRUSTLEDGER_API.md` with Platform probes section.
5. Run `bench ... run-tests` for `test_health` (and smoke TrustLedger suite if cheap).
6. Manual `curl -i /health` on a bench site.
7. Open PR using `docs/automation/pr-ai-disclosure-snippet.md`; link issue #2.
8. Verify: Copilot review against AC below; human confirms guest `GET /health`.

**Suggested commit:** `feat: add public GET /health probe endpoint`

---

## Acceptance-criteria traceability

| AC (issue #2) | Spec coverage | Implementation evidence |
|---------------|---------------|-------------------------|
| Endpoint responds on `GET /health` | §1 path; §2 `www/health.py` | Manual curl + I1 |
| Returns `200` and expected JSON fields | §1 schema; §4 U1–U3, I1–I3 | Tests + curl |
| Tests pass in CI | §4 test module + CI command | Green CI |
| Docs updated if route list documented | §5 `TRUSTLEDGER_API.md` | Doc diff in PR |
| Minimal / no auth / no DB / no observability / no breaking routes | §3 + handoff constraints | Review checklist |

See also: `docs/architecture/health-endpoint-handoff.md` for constraints, risks, assumptions, and DoD.
