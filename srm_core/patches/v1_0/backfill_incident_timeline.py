import frappe
from frappe.utils import get_datetime, now_datetime

from srm_core.services.timeline import (
	EVENT_INCIDENT_CREATED,
	EVENT_STATUS_CHANGED,
	build_event,
	emit_incident_event,
	make_idempotency_key,
)


def execute():
	created = 0
	status_events = 0
	now = now_datetime()

	for row in frappe.get_all(
		"SRM Incident",
		fields=["name", "incident_title", "status", "creation", "owner"],
	):
		created_key = make_idempotency_key(
			row.name,
			EVENT_INCIDENT_CREATED,
			{"incident": row.name, "status": row.status or "Draft"},
		)
		if not frappe.db.exists("SRM Incident Event", {"idempotency_key": created_key}):
			emit_incident_event(
				incident=row.name,
				event_type=EVENT_INCIDENT_CREATED,
				summary=f"Incident created: {row.incident_title}",
				details={"status": row.status, "backfill": True},
				actor=row.owner or "Administrator",
				event_time=get_datetime(row.creation or now),
				idempotency_key=created_key,
			)
			created += 1

		status_key = make_idempotency_key(
			row.name,
			EVENT_STATUS_CHANGED,
			{"incident": row.name, "status": row.status or "Draft", "backfill": True},
		)
		if row.status and not frappe.db.exists("SRM Incident Event", {"idempotency_key": status_key}):
			emit_incident_event(
				incident=row.name,
				event_type=EVENT_STATUS_CHANGED,
				summary=f"Status snapshot: {row.status}",
				details={
					"previous_status": None,
					"current_status": row.status,
					"backfill": True,
				},
				actor=row.owner or "Administrator",
				event_time=get_datetime(row.creation or now),
				idempotency_key=status_key,
			)
			status_events += 1

	frappe.db.commit()
	summary = f"Incident timeline backfill: created_events={created}, status_snapshot_events={status_events}"
	frappe.logger("srm_core").info(summary)
	print(summary)
