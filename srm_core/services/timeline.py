"""Incident timeline event helpers for SRM Core."""

import hashlib
import json

import frappe
from frappe.utils import cint, flt, get_datetime, now_datetime

from srm_core.services.attachments import diff_incident_attachments
from srm_core.services.comments import diff_incident_comments, parse_mention_users_field
from srm_core.services.risk_rollup import linked_risk_changed, residual_risk_materially_changed

EVENT_INCIDENT_CREATED = "INCIDENT_CREATED"
EVENT_STATUS_CHANGED = "STATUS_CHANGED"
EVENT_IMPACT_SCORED = "IMPACT_SCORED"
EVENT_PRIORITY_COMPUTED = "PRIORITY_COMPUTED"
EVENT_ESCALATION_CHANGED = "ESCALATION_CHANGED"
EVENT_SLA_UPDATED = "SLA_UPDATED"
EVENT_TASK_ADDED = "TASK_ADDED"
EVENT_TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
EVENT_COMMENT_ADDED = "COMMENT_ADDED"
EVENT_ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
EVENT_ATTACHMENT_REMOVED = "ATTACHMENT_REMOVED"
EVENT_RISK_LINKED = "RISK_LINKED"
EVENT_RESIDUAL_RISK_UPDATED = "RESIDUAL_RISK_UPDATED"

VALID_EVENT_TYPES = frozenset(
	{
		EVENT_INCIDENT_CREATED,
		EVENT_STATUS_CHANGED,
		EVENT_IMPACT_SCORED,
		EVENT_PRIORITY_COMPUTED,
		EVENT_ESCALATION_CHANGED,
		EVENT_SLA_UPDATED,
		EVENT_TASK_ADDED,
		EVENT_TASK_STATUS_CHANGED,
		EVENT_COMMENT_ADDED,
		EVENT_ATTACHMENT_ADDED,
		EVENT_ATTACHMENT_REMOVED,
		EVENT_RISK_LINKED,
		EVENT_RESIDUAL_RISK_UPDATED,
	}
)

SOURCE_SYSTEM = "system"
SOURCE_USER = "user"

SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_CRITICAL = "critical"


def serialize_details(details):
	if details is None:
		return None
	if isinstance(details, str):
		return details
	return json.dumps(details, sort_keys=True, default=str)


def build_event(
	incident,
	event_type,
	summary,
	details=None,
	actor=None,
	event_time=None,
	source=SOURCE_SYSTEM,
	idempotency_key=None,
	severity=SEVERITY_INFO,
):
	"""Build an unsaved SRM Incident Event document dict."""
	if event_type not in VALID_EVENT_TYPES:
		frappe.throw(f"Invalid incident event type: {event_type}")

	return {
		"doctype": "SRM Incident Event",
		"incident": incident,
		"event_type": event_type,
		"event_time": event_time or now_datetime(),
		"actor": actor or frappe.session.user,
		"summary": summary,
		"details_json": serialize_details(details),
		"source": source,
		"idempotency_key": idempotency_key,
		"severity": severity,
	}


def make_idempotency_key(incident, event_type, snapshot):
	"""Generate deterministic idempotency key for a transition snapshot."""
	payload = json.dumps(snapshot, sort_keys=True, default=str)
	digest = hashlib.sha256(f"{incident}|{event_type}|{payload}".encode()).hexdigest()[:32]
	return f"{incident}|{event_type}|{digest}"


def field_changed(previous, current, fieldname):
	previous_value = getattr(previous, fieldname, None) if previous else None
	current_value = getattr(current, fieldname, None)
	if fieldname in {"impact_score", "priority_score", "sla_target_hours"}:
		return flt(previous_value) != flt(current_value)
	if fieldname in {"sla_breached", "is_escalated", "requires_executive_attention"}:
		return cint(previous_value) != cint(current_value)
	if fieldname in {"sla_due_by", "sla_due_date"}:
		previous_dt = get_datetime(previous_value) if previous_value else None
		current_dt = get_datetime(current_value) if current_value else None
		return previous_dt != current_dt
	return previous_value != current_value


def child_row_key(row):
	if getattr(row, "name", None):
		return row.name
	return f"{row.idx}|{row.task_title}|{row.assignee}"


def diff_investigation_tasks(previous_rows, current_rows):
	"""Return added rows and status transitions for investigation tasks."""
	previous_rows = previous_rows or []
	current_rows = current_rows or []

	previous_by_key = {child_row_key(row): row for row in previous_rows}
	current_by_key = {child_row_key(row): row for row in current_rows}

	added = [row for key, row in current_by_key.items() if key not in previous_by_key]
	status_changes = []
	for key, current_row in current_by_key.items():
		previous_row = previous_by_key.get(key)
		if not previous_row:
			continue
		if previous_row.status != current_row.status:
			status_changes.append(
				{
					"task_key": key,
					"task_title": current_row.task_title,
					"assignee": current_row.assignee,
					"previous_status": previous_row.status,
					"current_status": current_row.status,
				}
			)

	return added, status_changes


def emit_incident_event(
	incident,
	event_type,
	summary,
	details=None,
	actor=None,
	event_time=None,
	source=SOURCE_SYSTEM,
	idempotency_key=None,
	severity=SEVERITY_INFO,
):
	"""Insert a timeline event if idempotency key is unused."""
	if idempotency_key and frappe.db.exists(
		"SRM Incident Event",
		{"idempotency_key": idempotency_key},
	):
		return None

	event_doc = frappe.get_doc(
		build_event(
			incident=incident,
			event_type=event_type,
			summary=summary,
			details=details,
			actor=actor,
			event_time=event_time,
			source=source,
			idempotency_key=idempotency_key,
			severity=severity,
		)
	)
	event_doc.insert(ignore_permissions=True)
	from srm_core.services.notifications import process_notifications_for_event

	process_notifications_for_event(event_doc)
	return event_doc


def get_incident_timeline(incident_name, limit=100):
	"""Return timeline events for an incident ordered by event_time descending.

	Callers must enforce authorization before invoking this helper, for example::

	    frappe.has_permission("SRM Incident", "read", incident_name, throw=True)
	    events = get_incident_timeline(incident_name)
	"""
	return frappe.get_all(
		"SRM Incident Event",
		filters={"incident": incident_name},
		fields=[
			"name",
			"incident",
			"event_type",
			"event_time",
			"actor",
			"summary",
			"details_json",
			"source",
			"idempotency_key",
			"severity",
		],
		order_by="event_time desc, creation desc",
		limit=limit,
	)


def severity_for_escalation(level):
	if level == "L3":
		return SEVERITY_CRITICAL
	if level in {"L2", "L1"}:
		return SEVERITY_WARN
	return SEVERITY_INFO


def emit_timeline_events_for_incident(doc, previous=None, is_insert=False):
	"""Emit timeline events based on incident diffs."""
	if not doc.name:
		return

	event_time = now_datetime()
	actor = frappe.session.user

	if is_insert:
		snapshot = {"incident": doc.name, "status": doc.status}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_INCIDENT_CREATED,
			summary=f"Incident created: {doc.incident_title}",
			details={"status": doc.status},
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_INCIDENT_CREATED, snapshot),
		)

	if not is_insert and field_changed(previous, doc, "status"):
		snapshot = {
			"previous_status": getattr(previous, "status", None),
			"current_status": doc.status,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_STATUS_CHANGED,
			summary=f"Status changed: {snapshot['previous_status']} -> {doc.status}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_STATUS_CHANGED, snapshot),
		)

	if is_insert or field_changed(previous, doc, "impact_score") or field_changed(previous, doc, "impact_band"):
		snapshot = {
			"impact_score": flt(doc.impact_score),
			"impact_band": doc.impact_band,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_IMPACT_SCORED,
			summary=f"Impact scored: {doc.impact_score} ({doc.impact_band})",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_IMPACT_SCORED, snapshot),
		)

	if is_insert or field_changed(previous, doc, "priority_score") or field_changed(previous, doc, "priority_level"):
		snapshot = {
			"priority_score": flt(doc.priority_score),
			"priority_level": doc.priority_level,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_PRIORITY_COMPUTED,
			summary=f"Priority computed: {doc.priority_level} ({doc.priority_score})",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_PRIORITY_COMPUTED, snapshot),
		)

	if is_insert or field_changed(previous, doc, "escalation_level") or field_changed(
		previous, doc, "is_escalated"
	):
		snapshot = {
			"previous_level": getattr(previous, "escalation_level", None),
			"current_level": doc.escalation_level,
			"is_escalated": cint(doc.is_escalated),
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_ESCALATION_CHANGED,
			summary=f"Escalation changed: {snapshot['previous_level']} -> {doc.escalation_level}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_ESCALATION_CHANGED, snapshot),
			severity=severity_for_escalation(doc.escalation_level),
		)

	sla_changed = is_insert or field_changed(previous, doc, "sla_target_hours") or field_changed(
		previous, doc, "sla_due_by"
	) or field_changed(previous, doc, "sla_due_date")
	if sla_changed:
		snapshot = {
			"sla_target_hours": flt(doc.sla_target_hours),
			"sla_due_by": str(get_datetime(doc.sla_due_by)) if doc.sla_due_by else None,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_SLA_UPDATED,
			summary=f"SLA updated: {doc.sla_target_hours}h due {doc.sla_due_by}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_SLA_UPDATED, snapshot),
			severity=SEVERITY_WARN if cint(doc.sla_breached) else SEVERITY_INFO,
		)

	previous_tasks = getattr(previous, "investigation_tasks", None) if previous else []
	added_tasks, status_changes = diff_investigation_tasks(previous_tasks, doc.investigation_tasks)

	for task in added_tasks:
		snapshot = {
			"task_key": child_row_key(task),
			"task_title": task.task_title,
			"assignee": task.assignee,
			"status": task.status,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_TASK_ADDED,
			summary=f"Task added: {task.task_title}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_TASK_ADDED, snapshot),
		)

	for change in status_changes:
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_TASK_STATUS_CHANGED,
			summary=(
				f"Task status changed: {change['task_title']} "
				f"({change['previous_status']} -> {change['current_status']})"
			),
			details=change,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_TASK_STATUS_CHANGED, change),
		)

	previous_comments = getattr(previous, "comments", None) if previous else []
	added_comments = diff_incident_comments(previous_comments, doc.comments)

	for comment in added_comments:
		mentions = parse_mention_users_field(comment.mention_users)
		snapshot = {
			"comment_id": comment.name or f"{comment.idx}|{comment.comment_on}",
			"is_internal": cint(comment.is_internal),
			"mention_count": len(mentions),
			"mentioned_users": sorted(mentions),
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_COMMENT_ADDED,
			summary=f"Comment added by {comment.comment_by or actor}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_COMMENT_ADDED, snapshot),
		)

	previous_attachments = getattr(previous, "attachments", None) if previous else []
	added_attachments, removed_attachments = diff_incident_attachments(
		previous_attachments,
		doc.attachments,
	)

	for attachment in added_attachments:
		snapshot = {
			"attachment_id": attachment.name or f"{attachment.idx}|{attachment.file_url}",
			"file_name": attachment.file_name,
			"evidence_type": attachment.evidence_type,
			"classification": attachment.classification,
			"is_primary_evidence": cint(attachment.is_primary_evidence),
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_ATTACHMENT_ADDED,
			summary=f"Attachment added: {attachment.file_name}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_ATTACHMENT_ADDED, snapshot),
		)

	for attachment in removed_attachments:
		snapshot = {
			"attachment_id": attachment.name,
			"file_name": attachment.file_name,
			"evidence_type": attachment.evidence_type,
			"classification": attachment.classification,
			"is_primary_evidence": cint(attachment.is_primary_evidence),
			"removal_reason": attachment.removal_reason,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_ATTACHMENT_REMOVED,
			summary=f"Attachment removed: {attachment.file_name}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_ATTACHMENT_REMOVED, snapshot),
		)

	if is_insert or linked_risk_changed(previous, doc):
		snapshot = {
			"linked_risk": doc.linked_risk,
			"risk_linked_on": str(get_datetime(doc.risk_linked_on)) if doc.risk_linked_on else None,
			"risk_linked_by": doc.risk_linked_by,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_RISK_LINKED,
			summary=f"Risk linked: {doc.linked_risk}",
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_RISK_LINKED, snapshot),
		)

	if doc.linked_risk and (is_insert or residual_risk_materially_changed(previous, doc)):
		snapshot = {
			"linked_risk": doc.linked_risk,
			"residual_risk_score": flt(doc.residual_risk_score),
			"residual_risk_band": doc.residual_risk_band,
			"previous_score": flt(getattr(previous, "residual_risk_score", 0)) if previous else None,
			"previous_band": getattr(previous, "residual_risk_band", None) if previous else None,
		}
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_RESIDUAL_RISK_UPDATED,
			summary=(
				f"Residual risk updated: {doc.residual_risk_score} ({doc.residual_risk_band})"
			),
			details=snapshot,
			actor=actor,
			event_time=event_time,
			idempotency_key=make_idempotency_key(doc.name, EVENT_RESIDUAL_RISK_UPDATED, snapshot),
			severity=SEVERITY_CRITICAL if doc.residual_risk_band == "Critical" else SEVERITY_INFO,
		)

