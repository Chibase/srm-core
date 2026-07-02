# SRM Core Operations Runbook

Operational commands for `srm_core` maintenance. All commands are **idempotent** and safe to re-run.

**Prerequisites:** SSH to bench host, activate bench, target site `sl2b.chibaseconsulting.co.za`.

**Permission:** System Manager role required at runtime.

---

## Rebuild incident timeline

Rebuild missing baseline timeline events (`INCIDENT_CREATED`, status snapshot) for incidents.

```bash
cd /home/frappe/frappe-bench
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.rebuild_incident_timeline
```

Single incident:

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.rebuild_incident_timeline --kwargs "{'incident': 'INC-00001'}"
```

Batch limit:

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.rebuild_incident_timeline --kwargs "{'limit': 200}"
```

**Expected output (dict):**

```json
{
  "operation": "rebuild_incident_timeline",
  "processed": 1,
  "created_events": 0,
  "status_snapshot_events": 0
}
```

Re-runs should return `created_events=0` and `status_snapshot_events=0` when baseline keys already exist.

---

## Requeue failed notifications

Reset failed notifications to `queued`, then dispatch stub delivery.

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.requeue_failed_notifications
```

With limit:

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.requeue_failed_notifications --kwargs "{'limit': 200}"
```

**Expected output:**

```json
{
  "operation": "requeue_failed_notifications",
  "requeued": 0,
  "dispatch": {"sent": 0, "failed": 0, "skipped": 0}
}
```

---

## Recompute residual risk

Recompute residual risk score/band/rationale for incidents with `linked_risk` set.

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.recompute_residual_risk
```

Single incident:

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.recompute_residual_risk --kwargs "{'incident': 'INC-00001'}"
```

**Expected output:**

```json
{
  "operation": "recompute_residual_risk",
  "processed": 1,
  "updated": 0
}
```

---

## Recompute priority and SLA

Recompute priority score/level and SLA targets (skips SLA mutation for Closed incidents).

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.recompute_priority_and_sla
```

**Expected output:**

```json
{
  "operation": "recompute_priority_and_sla",
  "processed": 1,
  "updated": 1
}
```

---

## Incident recovery snippets

### Duplicate timeline events suspected

1. Run rebuild (idempotent) — it only inserts missing idempotency keys.
2. Verify counts:

```bash
bench --site sl2b.chibaseconsulting.co.za mariadb -e "SELECT event_type, COUNT(*) FROM \`tabSRM Incident Event\` GROUP BY event_type;"
```

### Notifications stuck in failed

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.requeue_failed_notifications
```

### Residual risk drift after task changes

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.recompute_residual_risk --kwargs "{'limit': 500}"
```

### Priority/SLA drift after impact scoring changes

```bash
bench --site sl2b.chibaseconsulting.co.za execute srm_core.ops.maintenance.recompute_priority_and_sla --kwargs "{'limit': 500}"
```

---

## Safety notes

- All maintenance ops commit per batch and log summaries via `frappe.logger("srm_core")`.
- Timeline/notification inserts use deterministic idempotency keys; duplicate unique conflicts are skipped gracefully.
- Run `bench migrate` after deploy to apply invariant repair patch (`verify_and_repair_hardening_invariants`).
- Post-deploy verification:

```bash
bench --site sl2b.chibaseconsulting.co.za run-tests --app srm_core
```
