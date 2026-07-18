# TrustLedger API packet (srm-core)

> Whitelisted methods consumed by `trustledger-frontend` when `NEXT_PUBLIC_DATA_MODE=live`.
> Status: **implemented locally (Packet 16)** — run bench tests on Interserv before marking Done.

## Goals

1. Expose Frappe methods matching `docs/FRAPPE_API_CONTRACT.md` in the frontend repo.
2. Map existing `SRM Incident` (+ attachments, timeline events) to TrustLedger DTO shapes.
3. Provide project/notes stubs until Project Site / Engagement DocTypes exist.
4. Ship AI methods as **deterministic heuristics** first; swap to Grok when site config has an xAI key.

## Method paths

| Method | Module path |
|--------|-------------|
| `list_incidents` / `get_incident` / `list_evidence` | `srm_core.api.incidents` |
| `list_projects` / `get_project` | `srm_core.api.projects` |
| `list_meeting_notes` | `srm_core.api.engagements` |
| `suggest_triage` / `suggest_sentiment` / `draft_response` / `generate_report_brief` | `srm_core.api.ai` |
| `get_session` | `srm_core.api.auth` |

## Platform probes

| Path | Auth | Response |
|------|------|----------|
| `GET /health` | Guest allowed | `200` JSON: `status` (`"ok"`), `service` (`"srm-core"`), `timestamp` (ISO-8601 UTC) |
| `GET /ready` | Guest allowed | `200` when ready / `503` when not ready; JSON: `status` (`"ready"`\|`"not_ready"`), `service`, `timestamp`, `checks.db` / `checks.cache` (`ok`\|`fail`, optional `detail`) |

**Liveness (`/health`)**
- Implementation: `srm_core.www.health.HealthPageRenderer` + `srm_core.api.health.build_health_payload`
- Optional RPC alias: `/api/method/srm_core.api.health.health` (same payload)
- No DB / dependency checks; `Cache-Control: no-store`
- Spec: `docs/architecture/health-endpoint-spec.md`

**Readiness (`/ready`)**
- Implementation: `srm_core.www.ready.ReadyPageRenderer` + `srm_core.api.ready.build_ready_payload`
- Optional RPC alias: `/api/method/srm_core.api.ready.ready` (payload only; HTTP status via `GET /ready`)
- Lightweight checks: DB `select 1`, cache Redis ping; `Cache-Control: no-store`
- Spec: `docs/architecture/ready-endpoint-spec.md`

## Status mapping (DocType → TrustLedger)

| SRM Incident.status | TrustLedger status |
|---------------------|--------------------|
| Draft | Open |
| Open | Open |
| Under Investigation | Investigating |
| Resolved | Closed |
| Closed | Closed |
| (is_escalated and not terminal) | Escalated |

## Field notes

- Timeline uses `SRM Incident Event.event_time` (not a legacy `event_on`).
- Incident title comes from `incident_title`; priority from `priority_level` (`P4-Low`…`P1-Critical`).
- Evidence classification maps DocType `public|internal` → `General`, `confidential` → `Confidential`, `restricted` → `Restricted`.

## Quality gates

```bash
# On a Frappe bench with srm_core installed:
bench --site <SITE> run-tests --app srm_core --module srm_core.srm_core.tests.test_trustledger_api
```

## Out of scope (this packet)

- CORS / Interserv site config (ops)
- Real xAI network calls (feature-flagged stub only)
- New Project Site / Engagement DocTypes (use stubs)
