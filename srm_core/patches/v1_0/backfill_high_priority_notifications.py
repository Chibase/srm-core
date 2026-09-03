import frappe
from frappe.utils import add_to_date, now_datetime

from srm_core.services.notifications import (
	CHANNEL_EMAIL,
	CHANNEL_IN_APP,
	RULE_BOOTSTRAP_HIGH_PRIORITY,
	build_intent,
	make_notification_idempotency_key,
	queue_notifications,
)
from srm_core.services.priority import PRIORITY_P1_CRITICAL, PRIORITY_P2_HIGH


def execute():
	created = 0
	cutoff = add_to_date(now_datetime(), days=-30)
	incidents = frappe.get_all(
		"SRM Incident",
		filters={
			"creation": [">=", cutoff],
			"priority_level": ["in", [PRIORITY_P1_CRITICAL, PRIORITY_P2_HIGH]],
			"status": ["not in", ["Closed"]],
		},
		fields=["name", "incident_title", "incident_owner", "priority_level"],
	)

	for incident in incidents:
		recipients = set()
		if incident.incident_owner:
			recipients.add(incident.incident_owner)
		for user in frappe.get_all(
			"Has Role",
			filters={"role": "SRM Lead", "parenttype": "User"},
			pluck="parent",
		):
			recipients.add(user)

		intents = []
		subject = f"High-priority open incident: {incident.incident_title}"
		message = f"Bootstrap alert for {incident.priority_level} incident {incident.incident_title}."
		for recipient in recipients:
			for channel in (CHANNEL_IN_APP, CHANNEL_EMAIL):
				key = make_notification_idempotency_key(
					incident.name,
					None,
					recipient,
					channel,
					RULE_BOOTSTRAP_HIGH_PRIORITY,
				)
				if frappe.db.exists("SRM Notification", {"idempotency_key": key}):
					continue
				intent = build_intent(
					incident.name,
					None,
					recipient,
					channel,
					subject,
					message,
					RULE_BOOTSTRAP_HIGH_PRIORITY,
				)
				if intent:
					intents.append(intent)

		created += len(queue_notifications(intents))

	frappe.db.commit()
	summary = f"Notification bootstrap backfill: created={created}"
	frappe.logger("srm_core").info(summary)
	print(summary)
