"""Notification rule evaluation and delivery stubs for SRM Core."""

import hashlib
import json

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from srm_core.services.investigation_tasks import BLOCKING_TASK_STATUSES
from srm_core.services.permissions import user_has_notification_privileged_role
from srm_core.services.priority import PRIORITY_P1_CRITICAL
from srm_core.services.statuses import INCIDENT_CLOSED
from srm_core.services.timeline import (
	EVENT_COMMENT_ADDED,
	EVENT_ESCALATION_CHANGED,
	EVENT_PRIORITY_COMPUTED,
	EVENT_SLA_UPDATED,
	EVENT_STATUS_CHANGED,
)

CHANNEL_IN_APP = "in_app"
CHANNEL_EMAIL = "email"
NOTIFICATION_CHANNELS = (CHANNEL_IN_APP, CHANNEL_EMAIL)

STATUS_QUEUED = "queued"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

RULE_ESCALATION_L2_L3 = "escalation_l2_l3"
RULE_SLA_DUE_6H = "sla_due_within_6h"
RULE_STATUS_CLOSED = "status_closed"
RULE_PRIORITY_P1 = "priority_p1"
RULE_BOOTSTRAP_HIGH_PRIORITY = "bootstrap_high_priority"
RULE_COMMENT_MENTION = "comment_mention"

ESCALATION_NOTIFY_LEVELS = frozenset({"L2", "L3"})
SLA_WARNING_HOURS = 6


def parse_event_details(event_doc):
	raw = getattr(event_doc, "details_json", None)
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, json.JSONDecodeError):
		return {}


def make_notification_idempotency_key(incident, event, recipient, channel, rule_key):
	payload = f"{incident}|{event or ''}|{recipient}|{channel}|{rule_key}"
	return hashlib.sha256(payload.encode()).hexdigest()


def get_users_with_role(role_name):
	return frappe.get_all(
		"Has Role",
		filters={"role": role_name, "parenttype": "User"},
		pluck="parent",
	)


def get_open_task_assignees(incident_doc):
	assignees = set()
	for row in incident_doc.get("investigation_tasks") or []:
		if row.status in BLOCKING_TASK_STATUSES and row.assignee:
			assignees.add(row.assignee)
	return assignees


def get_task_assignees(incident_doc):
	assignees = set()
	for row in incident_doc.get("investigation_tasks") or []:
		if row.assignee:
			assignees.add(row.assignee)
	return assignees


def build_intent(incident, event_name, recipient, channel, subject, message, rule_key):
	if not recipient:
		return None
	return {
		"incident": incident,
		"event": event_name,
		"recipient": recipient,
		"channel": channel,
		"subject": subject,
		"message": message,
		"rule_key": rule_key,
	}


def add_recipient_intents(intents, seen, incident, event_name, recipient, subject, message, rule_key):
	if not recipient:
		return
	for channel in NOTIFICATION_CHANNELS:
		key = (recipient, channel, rule_key)
		if key in seen:
			continue
		seen.add(key)
		intent = build_intent(incident, event_name, recipient, channel, subject, message, rule_key)
		if intent:
			intents.append(intent)


def evaluate_incident_event_for_notifications(event_doc):
	"""Return notification intents for a timeline event."""
	event_type = event_doc.event_type
	incident_name = event_doc.incident
	details = parse_event_details(event_doc)
	incident = frappe.get_doc("SRM Incident", incident_name)
	intents = []
	seen = set()

	if event_type == EVENT_ESCALATION_CHANGED:
		current_level = details.get("current_level")
		if current_level in ESCALATION_NOTIFY_LEVELS:
			subject = f"Escalation alert: {incident.incident_title} is {current_level}"
			message = event_doc.summary
			add_recipient_intents(
				intents,
				seen,
				incident_name,
				event_doc.name,
				incident.incident_owner,
				subject,
				message,
				RULE_ESCALATION_L2_L3,
			)
			for assignee in get_open_task_assignees(incident):
				add_recipient_intents(
					intents,
					seen,
					incident_name,
					event_doc.name,
					assignee,
					subject,
					message,
					RULE_ESCALATION_L2_L3,
				)

	elif event_type == EVENT_SLA_UPDATED:
		sla_due_by = details.get("sla_due_by") or incident.sla_due_by
		if sla_due_by:
			due = get_datetime(sla_due_by)
			window_end = add_to_date(now_datetime(), hours=SLA_WARNING_HOURS)
			if due <= window_end:
				subject = f"SLA due soon: {incident.incident_title}"
				message = event_doc.summary
				add_recipient_intents(
					intents,
					seen,
					incident_name,
					event_doc.name,
					incident.incident_owner,
					subject,
					message,
					RULE_SLA_DUE_6H,
				)

	elif event_type == EVENT_STATUS_CHANGED:
		if details.get("current_status") == INCIDENT_CLOSED:
			subject = f"Incident closed: {incident.incident_title}"
			message = event_doc.summary
			recipients = set()
			if incident.incident_owner:
				recipients.add(incident.incident_owner)
			recipients.update(get_task_assignees(incident))
			for recipient in recipients:
				add_recipient_intents(
					intents,
					seen,
					incident_name,
					event_doc.name,
					recipient,
					subject,
					message,
					RULE_STATUS_CLOSED,
				)

	elif event_type == EVENT_PRIORITY_COMPUTED:
		if details.get("priority_level") == PRIORITY_P1_CRITICAL:
			subject = f"Critical priority: {incident.incident_title}"
			message = event_doc.summary
			recipients = set()
			if incident.incident_owner:
				recipients.add(incident.incident_owner)
			recipients.update(get_users_with_role("SRM Lead"))
			for recipient in recipients:
				add_recipient_intents(
					intents,
					seen,
					incident_name,
					event_doc.name,
					recipient,
					subject,
					message,
					RULE_PRIORITY_P1,
				)

	elif event_type == EVENT_COMMENT_ADDED:
		actor = event_doc.actor or frappe.session.user
		mentioned_users = details.get("mentioned_users") or []
		subject = f"You were mentioned on {incident.incident_title}"
		message = event_doc.summary
		for recipient in mentioned_users:
			if not recipient or recipient == actor:
				continue
			if not frappe.db.exists("User", recipient):
				continue
			add_recipient_intents(
				intents,
				seen,
				incident_name,
				event_doc.name,
				recipient,
				subject,
				message,
				RULE_COMMENT_MENTION,
			)

	return intents


def queue_notifications(intents):
	"""Persist notification rows with idempotency guard."""
	queued = []
	now = now_datetime()
	for intent in intents or []:
		idempotency_key = make_notification_idempotency_key(
			intent["incident"],
			intent.get("event"),
			intent["recipient"],
			intent["channel"],
			intent["rule_key"],
		)
		if frappe.db.exists("SRM Notification", {"idempotency_key": idempotency_key}):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "SRM Notification",
				"incident": intent["incident"],
				"event": intent.get("event"),
				"recipient": intent["recipient"],
				"channel": intent["channel"],
				"subject": intent["subject"],
				"message": intent["message"],
				"status": STATUS_QUEUED,
				"queued_on": now,
				"rule_key": intent["rule_key"],
				"idempotency_key": idempotency_key,
			}
		)
		doc.insert(ignore_permissions=True)
		queued.append(doc.name)
	return queued


def dispatch_queued_notifications(limit=100):
	"""Stub dispatcher for queued notifications."""
	results = {"sent": 0, "failed": 0, "skipped": 0}
	now = now_datetime()
	rows = frappe.get_all(
		"SRM Notification",
		filters={"status": STATUS_QUEUED},
		fields=["name", "channel", "recipient"],
		order_by="queued_on asc",
		limit=limit,
	)

	for row in rows:
		if row.channel == CHANNEL_IN_APP:
			_update_notification_status(row.name, STATUS_SENT, sent_on=now)
			results["sent"] += 1
			continue

		if row.channel == CHANNEL_EMAIL:
			email = frappe.db.get_value("User", row.recipient, "email")
			if email:
				_update_notification_status(row.name, STATUS_SENT, sent_on=now)
				results["sent"] += 1
			else:
				_update_notification_status(
					row.name,
					STATUS_FAILED,
					failure_reason="Recipient has no email address.",
				)
				results["failed"] += 1
			continue

		_update_notification_status(row.name, STATUS_SKIPPED, failure_reason="Unknown channel.")
		results["skipped"] += 1

	return results


def _update_notification_status(name, status, sent_on=None, failure_reason=None):
	frappe.flags.srm_notification_system_update = True
	values = {"status": status}
	if sent_on:
		values["sent_on"] = sent_on
	if failure_reason:
		values["failure_reason"] = failure_reason
	frappe.db.set_value("SRM Notification", name, values, update_modified=False)
	frappe.flags.srm_notification_system_update = False


def process_notifications_for_event(event_doc):
	"""Evaluate, queue, and dispatch notifications for a timeline event."""
	if not event_doc or not event_doc.name:
		return {"queued": [], "dispatch": {}}
	intents = evaluate_incident_event_for_notifications(event_doc)
	queued = queue_notifications(intents)
	dispatch = dispatch_queued_notifications() if queued else {"sent": 0, "failed": 0, "skipped": 0}
	return {"queued": queued, "dispatch": dispatch}


def get_unread_in_app_notifications(user, limit=50):
	"""Return unread in-app notifications for a user."""
	return frappe.get_all(
		"SRM Notification",
		filters={
			"recipient": user,
			"channel": CHANNEL_IN_APP,
			"is_read": 0,
			"status": STATUS_SENT,
		},
		fields=[
			"name",
			"incident",
			"event",
			"subject",
			"message",
			"queued_on",
			"sent_on",
			"rule_key",
		],
		order_by="sent_on desc, queued_on desc",
		limit=limit,
	)


def mark_notification_read(notification_name, user=None):
	"""Mark a notification read for the recipient or a privileged user."""
	user = user or frappe.session.user
	notification = frappe.get_doc("SRM Notification", notification_name)
	if notification.recipient != user and not user_has_notification_privileged_role(user):
		frappe.throw(_("You do not have permission to mark this notification as read."))

	frappe.flags.srm_notification_system_update = True
	frappe.db.set_value(
		"SRM Notification",
		notification_name,
		{"is_read": 1, "read_on": now_datetime()},
		update_modified=False,
	)
	frappe.flags.srm_notification_system_update = False
	return notification_name
