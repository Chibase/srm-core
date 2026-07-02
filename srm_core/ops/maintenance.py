"""Bench-executable maintenance operations for SRM Core."""

import frappe
from frappe import _
from frappe.utils import add_to_date, flt, get_datetime, now_datetime

from srm_core.services.notifications import (
	STATUS_FAILED,
	STATUS_QUEUED,
	dispatch_queued_notifications,
)
from srm_core.services.permissions import user_has_system_manager_role
from srm_core.services.priority import (
	compute_priority_score,
	priority_band,
	resolve_sentiment_signal,
	sla_hours_for_priority,
)
from srm_core.services.risk_rollup import apply_incident_risk_linkage
from srm_core.services.statuses import INCIDENT_CLOSED
from srm_core.services.timeline import (
	EVENT_INCIDENT_CREATED,
	EVENT_STATUS_CHANGED,
	emit_incident_event,
	make_idempotency_key,
)


def _require_system_manager():
	if not user_has_system_manager_role():
		frappe.throw(_("Only System Manager can run this maintenance operation."))


def _incident_names(incident=None, limit=500):
	if incident:
		return [incident]
	return frappe.get_all("SRM Incident", pluck="name", limit=limit, order_by="modified desc")


@frappe.whitelist()
def rebuild_incident_timeline(incident=None, limit=500):
	"""Rebuild missing baseline timeline events idempotently."""
	_require_system_manager()
	limit = int(limit or 500)
	created = 0
	status_events = 0
	processed = 0
	now = now_datetime()

	for name in _incident_names(incident=incident, limit=limit):
		row = frappe.db.get_value(
			"SRM Incident",
			name,
			["name", "incident_title", "status", "creation", "owner"],
			as_dict=True,
		)
		if not row:
			continue
		processed += 1
		status = row.status or "Draft"

		created_key = make_idempotency_key(
			row.name,
			EVENT_INCIDENT_CREATED,
			{"incident": row.name, "status": status},
		)
		if not frappe.db.exists("SRM Incident Event", {"idempotency_key": created_key}):
			emit_incident_event(
				incident=row.name,
				event_type=EVENT_INCIDENT_CREATED,
				summary=f"Incident created: {row.incident_title}",
				details={"status": status, "maintenance_rebuild": True},
				actor=row.owner or frappe.session.user,
				event_time=get_datetime(row.creation or now),
				idempotency_key=created_key,
			)
			created += 1

		status_key = make_idempotency_key(
			row.name,
			EVENT_STATUS_CHANGED,
			{"incident": row.name, "status": status, "maintenance_rebuild": True},
		)
		if status and not frappe.db.exists("SRM Incident Event", {"idempotency_key": status_key}):
			emit_incident_event(
				incident=row.name,
				event_type=EVENT_STATUS_CHANGED,
				summary=f"Status snapshot: {status}",
				details={
					"previous_status": None,
					"current_status": status,
					"maintenance_rebuild": True,
				},
				actor=row.owner or frappe.session.user,
				event_time=get_datetime(row.creation or now),
				idempotency_key=status_key,
			)
			status_events += 1

	frappe.db.commit()
	summary = {
		"operation": "rebuild_incident_timeline",
		"processed": processed,
		"created_events": created,
		"status_snapshot_events": status_events,
	}
	frappe.logger("srm_core").info(summary)
	return summary


@frappe.whitelist()
def requeue_failed_notifications(limit=500):
	"""Requeue failed notifications and dispatch queued rows."""
	_require_system_manager()
	limit = int(limit or 500)
	requeued = 0
	rows = frappe.get_all(
		"SRM Notification",
		filters={"status": STATUS_FAILED},
		fields=["name"],
		limit=limit,
		order_by="modified asc",
	)
	for row in rows:
		frappe.db.set_value(
			"SRM Notification",
			row.name,
			{
				"status": STATUS_QUEUED,
				"failure_reason": None,
				"queued_on": now_datetime(),
			},
			update_modified=False,
		)
		requeued += 1

	dispatch = dispatch_queued_notifications(limit=limit)
	frappe.db.commit()
	summary = {
		"operation": "requeue_failed_notifications",
		"requeued": requeued,
		"dispatch": dispatch,
	}
	frappe.logger("srm_core").info(summary)
	return summary


@frappe.whitelist()
def recompute_residual_risk(incident=None, limit=500):
	"""Recompute residual risk fields for linked incidents."""
	_require_system_manager()
	limit = int(limit or 500)
	filters = {"linked_risk": ["is", "set"]}
	if incident:
		filters["name"] = incident

	updated = 0
	processed = 0
	for row in frappe.get_all("SRM Incident", filters=filters, fields=["name"], limit=limit):
		doc = frappe.get_doc("SRM Incident", row.name)
		previous_score = doc.residual_risk_score
		previous_band = doc.residual_risk_band
		apply_incident_risk_linkage(doc, previous=doc)
		processed += 1
		if doc.residual_risk_score != previous_score or doc.residual_risk_band != previous_band:
			updated += 1

	frappe.db.commit()
	summary = {
		"operation": "recompute_residual_risk",
		"processed": processed,
		"updated": updated,
	}
	frappe.logger("srm_core").info(summary)
	return summary


@frappe.whitelist()
def recompute_priority_and_sla(incident=None, limit=500):
	"""Recompute priority score/level and SLA targets for incidents."""
	_require_system_manager()
	limit = int(limit or 500)
	now = now_datetime()
	updated = 0
	processed = 0

	for name in _incident_names(incident=incident, limit=limit):
		doc = frappe.get_doc("SRM Incident", name)
		processed += 1
		sentiment = resolve_sentiment_signal(
			doc.name,
			doc.geographic_area,
			reference_datetime=doc.creation or now,
		)
		priority_score = compute_priority_score(flt(doc.impact_score), sentiment)
		priority_level = priority_band(priority_score)
		values = {
			"priority_score": priority_score,
			"priority_level": priority_level,
			"priority_computed_on": now,
			"priority_computed_by": frappe.session.user,
		}
		if doc.status != INCIDENT_CLOSED:
			sla_hours = sla_hours_for_priority(priority_level)
			base = get_datetime(doc.creation or now)
			sla_due_by = add_to_date(base, hours=sla_hours)
			values.update(
				{
					"sla_target_hours": sla_hours,
					"sla_due_by": sla_due_by,
					"sla_due_date": sla_due_by,
				}
			)
		frappe.db.set_value("SRM Incident", doc.name, values, update_modified=False)
		updated += 1

	frappe.db.commit()
	summary = {
		"operation": "recompute_priority_and_sla",
		"processed": processed,
		"updated": updated,
	}
	frappe.logger("srm_core").info(summary)
	return summary
