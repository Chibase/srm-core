import frappe

from srm_core.services.idempotency import fallback_idempotency_key
from srm_core.services.investigation_tasks import TASK_STATUS_OPEN, VALID_TASK_STATUSES
from srm_core.services.notifications import make_notification_idempotency_key
from srm_core.services.statuses import INCIDENT_DRAFT
from srm_core.services.timeline import VALID_EVENT_TYPES


def execute():
	event_keys_repaired = _repair_missing_event_idempotency_keys()
	notification_keys_repaired = _repair_missing_notification_idempotency_keys()
	incident_status_repaired = _repair_blank_incident_statuses()
	task_status_repaired = _repair_blank_task_statuses()
	invalid_event_types = _count_invalid_event_types()

	frappe.db.commit()
	summary = (
		f"Hardening invariant repair: event_keys={event_keys_repaired}, "
		f"notification_keys={notification_keys_repaired}, "
		f"incident_status={incident_status_repaired}, task_status={task_status_repaired}, "
		f"invalid_event_types={invalid_event_types}"
	)
	frappe.logger("srm_core").info(summary)
	print(summary)


def _repair_missing_event_idempotency_keys():
	repaired = 0
	for row in frappe.get_all(
		"SRM Incident Event",
		filters={"idempotency_key": ["in", ["", None]]},
		fields=["name", "incident", "event_type", "event_time"],
	):
		key = fallback_idempotency_key(
			"SRM Incident Event",
			row.name,
			row.incident,
			row.event_type,
			row.event_time,
		)
		if frappe.db.exists("SRM Incident Event", {"idempotency_key": key}):
			key = fallback_idempotency_key(key, "repair", row.name)
		frappe.db.set_value(
			"SRM Incident Event",
			row.name,
			"idempotency_key",
			key,
			update_modified=False,
		)
		repaired += 1
	return repaired


def _repair_missing_notification_idempotency_keys():
	repaired = 0
	for row in frappe.get_all(
		"SRM Notification",
		filters={"idempotency_key": ["in", ["", None]]},
		fields=["name", "incident", "event", "recipient", "channel", "rule_key"],
	):
		key = make_notification_idempotency_key(
			row.incident,
			row.event,
			row.recipient,
			row.channel,
			row.rule_key,
		)
		if frappe.db.exists("SRM Notification", {"idempotency_key": key}):
			key = fallback_idempotency_key(key, "repair", row.name)
		frappe.db.set_value(
			"SRM Notification",
			row.name,
			"idempotency_key",
			key,
			update_modified=False,
		)
		repaired += 1
	return repaired


def _repair_blank_incident_statuses():
	repaired = 0
	for row in frappe.get_all(
		"SRM Incident",
		filters={"status": ["in", ["", None]]},
		pluck="name",
	):
		frappe.db.set_value(
			"SRM Incident",
			row,
			"status",
			INCIDENT_DRAFT,
			update_modified=False,
		)
		repaired += 1
	return repaired


def _repair_blank_task_statuses():
	repaired = 0
	for row in frappe.get_all(
		"SRM Investigation Task",
		filters={"status": ["in", ["", None]]},
		fields=["name", "parent"],
	):
		frappe.db.set_value(
			"SRM Investigation Task",
			row.name,
			"status",
			TASK_STATUS_OPEN,
			update_modified=False,
		)
		repaired += 1
	return repaired


def _count_invalid_event_types():
	invalid = 0
	for row in frappe.get_all("SRM Incident Event", fields=["name", "event_type"]):
		if row.event_type not in VALID_EVENT_TYPES:
			invalid += 1
			frappe.logger("srm_core").warning(
				"Invalid SRM Incident Event type %s on %s",
				row.event_type,
				row.name,
			)
	return invalid
