# Spec: GET `/ready` — Readiness Probe

**Related:** Issue intake (Gemini Spec) — readiness after liveness `#2` / `GET /health`  
**Companion handoff:** `docs/architecture/ready-endpoint-handoff.md`  
**Pattern to mirror:** `docs/architecture/health-endpoint-spec.md` + shipped `srm_core/www/health.py`

**Repo reality:** SRM Core is a Frappe app. `GET /health` already uses `HealthPageRenderer` + `srm_core.api.health`. Readiness must stay on the same public JSON probe pattern, but **may** perform lightweight dependency I/O (unlike liveness).

---

## 1) Endpoint Contract

| Item | Spec |
|------|------|
| Method / path | `GET /ready` |
| Auth | Public / guest-allowed |
| Ready status | `200` |
| Not-ready status | `503` |
| Content-Type | `application/json; charset=utf-8` |
| Caching | `Cache-Control: no-store` |
| Side effects | Read-only pings only; no writes, no auth mutations |

### JSON body (exact top-level fields)

```json
{
  "status": "ready",
  "service": "srm-core",
  "timestamp": "2026-07-18T16:00:00Z",
  "checks": {
    "db": { "status": "ok" },
    "cache": { "status": "ok" }
  }
}
```

| Field | Type | Rules |
|-------|------|--------|
| `status` | string | `"ready"` iff **all** required checks are `"ok"`; otherwise `"not_ready"` |
| `service` | string | Always `"srm-core"` |
| `timestamp` | string | ISO-8601 UTC at request time (`Z` or `+00:00`) |
| `checks` | object | One entry per required dependency (keys below) |

### Per-check object

```ts
db: { status: "ok" | "fail", detail?: string }
cache: { status: "ok" | "fail", detail?: string }
```

| Field | Type | Rules |
|-------|------|--------|
| `status` | string | `"ok"` or `"fail"` only |
| `detail` | string | **Optional**, short, non-sensitive (e.g. `"timeout"`). Omit when `status` is `"ok"`. No stack traces, no DSNs, no secrets. |

### HTTP ↔ payload coupling

| Condition | HTTP | `status` field |
|-----------|------|----------------|
| All required checks `"ok"` | `200` | `"ready"` |
| Any required check `"fail"` | `503` | `"not_ready"` |

Never return `200` with `"not_ready"`, or `503` with `"ready"`.

---

## 2) Architecture Fit

### Required dependency checks (v1)

| Key | Meaning | Lightweight check (Frappe-consistent) |
|-----|---------|----------------------------------------|
| `db` | MariaDB/MySQL site DB | `frappe.db.sql("select 1")` (or equivalent one-row ping) |
| `cache` | Frappe cache Redis | `frappe.cache().ping()` (or `frappe.cache.ping()` per installed Frappe API) |

**Out of v1 required set:** Redis queue, socketio, external HTTP, filesystem, Grok/xAI, S3.

### Files to add/change

| Layer | Path | Role |
|-------|------|------|
| Check + payload | `srm_core/api/ready.py` | `check_db()`, `check_cache()`, `run_readiness_checks()`, `build_ready_payload()` → `(payload: dict, http_status: int)` |
| Public route | `srm_core/www/ready.py` | `ReadyPageRenderer` — same Response pattern as `HealthPageRenderer` |
| Hooks | `srm_core/hooks.py` | Append `"srm_core.www.ready.ReadyPageRenderer"` to existing `page_renderer` list |
| Tests | `srm_core/srm_core/tests/test_ready.py` | Ready + not-ready paths |
| Docs | `docs/TRUSTLEDGER_API.md` Platform probes + README one-liner |

**Do not** implement under empty `apps/api/`.  
**Do not** modify `/health` contract.

### Framework conventions

- Mirror `srm_core/www/health.py`: `BaseRenderer`, `can_render` for path `ready`, `Response` with JSON body + `Cache-Control: no-store`.
- Keep check functions **injectable/mockable** (pure-ish) so tests can force fail without killing CI DB/Redis.
- Optional: `@frappe.whitelist(allow_guest=True) def ready()` returning payload only (HTTP status still owned by www renderer). Primary contract remains `GET /ready`.
- Timeouts: prefer fail-fast; if Frappe client has no timeout knob, rely on short query/ping and catch exceptions as `"fail"`.
- Catch exceptions per check; never let an uncaught dependency error become an opaque 500 if a structured `503` payload can be returned.

### Suggested internal shape (no production code in this spec)

- `run_readiness_checks() -> dict[str, dict]` building `checks`
- `build_ready_payload() -> tuple[dict, int]` deriving overall `status` + HTTP code
- Renderer calls `build_ready_payload()` and sets `Response(..., status=http_status)`

---

## 3) Error / Edge Cases

| Case | Expected |
|------|----------|
| DB up, Redis up | `200` / `"ready"` / both checks `"ok"` |
| DB down or query throws | `503` / `"not_ready"` / `checks.db.status == "fail"` |
| Cache Redis ping fails | `503` / `"not_ready"` / `checks.cache.status == "fail"` |
| Both fail | `503` / both `"fail"` |
| Check raises unexpected exception | Mark that check `"fail"`; still return JSON `503` (not HTML 500) |
| Guest vs logged-in | Identical behavior |
| Liveness still works when not ready | `/health` remains `200`/`ok` (process up); `/ready` may be `503` |
| Slow dependency | Treat as fail if it errors/times out; do not hang the worker indefinitely |
| Detail leakage | No connection strings, passwords, host internals in `detail` |
| Backward compatibility | Additive route only; no changes to existing `/api/method/srm_core.api.*` or `/health` |

---

## 4) Test Specification

**File:** `srm_core/srm_core/tests/test_ready.py`

### Unit

| ID | Case | Assertions |
|----|------|------------|
| U1 | All checks ok (real or stubbed) | `status == "ready"`; HTTP helper returns `200`; `checks.db` + `checks.cache` both `"ok"` |
| U2 | DB check forced fail | `status == "not_ready"`; HTTP `503`; `checks.db.status == "fail"`; cache may still `"ok"` |
| U3 | Cache check forced fail | Symmetric to U2 for `checks.cache` |
| U4 | Payload shape | Top-level keys exactly `status`, `service`, `timestamp`, `checks`; check keys exactly `db`, `cache`; `service == "srm-core"`; timestamp ISO-parseable |
| U5 | Coupling | Never `"ready"` with any `"fail"`; never `"not_ready"` with all `"ok"` |

### Integration / HTTP

| ID | Case | Assertions |
|----|------|------------|
| I1 | `GET /ready` as Guest when env healthy | `200`, `application/json`, body matches ready contract |
| I2 | `GET /ready` with mocked failing check | `503` + `not_ready` payload (patch check fn before `get_response`) |

**CI command:**

```bash
bench --site <SITE> run-tests --app srm_core --module srm_core.srm_core.tests.test_ready
```

**Manual:**

```bash
curl -i https://<site>/ready
# Simulate failure in staging only (e.g. stop redis briefly) and re-curl — expect 503
```

---

## 5) Documentation Updates

| File | Change |
|------|--------|
| `docs/TRUSTLEDGER_API.md` | Extend **Platform probes** with `GET /ready` (200/503 + checks) |
| `README.md` | Add one-liner next to `/health` probe note |
| `docs/architecture/ready-endpoint-handoff.md` | Constraints / risks / DoD (companion) |

---

## 6) Rollback Plan

1. Revert merge commit / remove `api/ready.py`, `www/ready.py`, hooks entry, tests, doc lines.
2. No migrations or permission changes.
3. Orchestrators using `/ready` should fall back to prior probe policy or temporarily use `/health` only.
4. `/health` and TrustLedger RPC routes unaffected.

---

## 7) Execution Plan (Cursor checklist)

1. Add `srm_core/api/ready.py` with isolated check helpers + `build_ready_payload()`.
2. Add `srm_core/www/ready.py` `ReadyPageRenderer` mirroring health Response pattern (status from payload builder).
3. Register renderer in `srm_core/hooks.py` `page_renderer` list.
4. Add `test_ready.py` covering U1–U5 and I1–I2 (mock fails for not-ready).
5. Update `docs/TRUSTLEDGER_API.md` + README probe line.
6. Run bench tests for `test_ready` (+ smoke `test_health`).
7. Manual `curl -i /ready` on healthy site.
8. PR with AI disclosure; link issue; note rollback.

**Suggested commits:**

- `feat(api): add GET /ready readiness endpoint`
- `test(api): add coverage for readiness ready and not-ready paths`
- `docs: document GET /ready readiness probe`

---

## Acceptance-criteria traceability

| AC | Spec | Evidence |
|----|------|----------|
| `GET /ready` exists and is public | §1, §2 www renderer | I1 Guest |
| 200 + payload when deps available | §1 coupling, §4 U1/I1 | Tests + curl |
| 503 + payload when dep unavailable | §1, §4 U2/U3/I2 | Mocked fail tests |
| `checks` ok/fail per dependency (`db`, `cache`) | §1 per-check object | U2/U3 |
| Tests cover both paths | §4 | `test_ready.py` |
| CI passes | §4 CI command | PR checks |
| Docs updated | §5 | TRUSTLEDGER_API + README |
| Minimal / no auth / no deep diagnostics / no breaking routes | §3 + handoff | Review |

---

## Context (issue intake)

We already have `/health` for liveness. Orchestrators need `/ready` so traffic is routed only when DB + cache Redis are usable. Deep diagnostics, auth changes, observability platforms, and new infra are out of scope.
