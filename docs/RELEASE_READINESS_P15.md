# Release Readiness — Packet 15 (Production Hardening)

**Branch:** `develop`  
**Scope:** Packets 06–14 hardening pass

---

## What was hardened

| Area | Change |
|------|--------|
| Idempotency | Shared `services/idempotency.py` with duplicate detection + graceful insert skip |
| Timeline | `emit_incident_event` handles unique conflicts without duplicate notifications |
| Notifications | `queue_notifications` uses shared safe insert + pre-check |
| Escalation backfill | Idempotent skip when unchanged; preserves manual reasons via `resolve_escalation_reason` |
| Residual risk | Persist only when linked/unlinked; deterministic recompute |
| Data integrity | `idempotency_key` unique + indexed on events/notifications |
| Enum drift | `VALID_INCIDENT_STATUSES` validation on incident save |
| Repair patch | Backfills missing idempotency keys; repairs blank statuses |
| Operations | `srm_core/ops/maintenance.py` bench entrypoints (System Manager gated) |

---

## Invariant checklist

- [ ] `bench migrate` completes without error
- [ ] `verify_and_repair_hardening_invariants` patch runs once (logged in migrate output)
- [ ] `bench run-tests --app srm_core` → all green (~120 tests)
- [ ] No duplicate `idempotency_key` rows in `SRM Incident Event` or `SRM Notification`
- [ ] Maintenance ops return stable summaries on re-run (`created_events=0`, `updated=0`)
- [ ] Critical residual close-gate still blocks non–System Manager
- [ ] Timeline events append-only (no manual insert except System Manager)

---

## Rollback notes

- **Schema:** Packet 15 adds indexes on existing unique fields and a repair patch only — no destructive DDL.
- **Code rollback:** Revert to prior `develop` commit and `bench migrate` (patch is idempotent; safe on re-upgrade).
- **Data:** Repair patch only fills missing keys/defaults; does not delete rows.
- **Risk:** If rolled back, duplicate-insert race protection reverts to pre-P15 check-only behavior.

---

## Post-deploy verification commands

```bash
cd /home/frappe/frappe-bench
bench --site sl2b.chibaseconsulting.co.za migrate
bench --site sl2b.chibaseconsulting.co.za run-tests --app srm_core
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.rebuild_incident_timeline --kwargs "{'limit': 5}"
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.recompute_residual_risk --kwargs "{'limit': 5}"
```

SQL spot checks:

```sql
SELECT COUNT(*) AS missing_event_keys FROM `tabSRM Incident Event` WHERE IFNULL(idempotency_key,'')='';
SELECT COUNT(*) AS missing_notification_keys FROM `tabSRM Notification` WHERE IFNULL(idempotency_key,'')='';
SELECT COUNT(*) AS blank_status FROM `tabSRM Incident` WHERE IFNULL(status,'')='';
```

All counts should be `0` after repair patch.

---

## Ops reference

See [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md) for full command reference and recovery playbooks.
