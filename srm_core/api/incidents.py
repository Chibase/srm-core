"""TrustLedger incident API (whitelisted)."""

from __future__ import annotations

import frappe
from frappe import _

from srm_core.api.serializers import serialize_evidence_row, serialize_incident


def _as_bool(value):
	if value in (True, 1, "1", "true", "True", "yes"):
		return True
	if value in (False, 0, "0", "false", "False", "no", None, ""):
		return False
	return bool(value)


@frappe.whitelist()
def list_incidents(
	ward=None,
	projectId=None,
	status=None,
	priority=None,
	slaBreached=None,
	escalatedOnly=None,
):
	"""Return TrustLedger-shaped incident list."""
	frappe.has_permission("SRM Incident", "read", throw=True)

	filters = {}
	if projectId:
		filters["project"] = projectId
	if priority:
		filters["priority_level"] = priority
	if _as_bool(slaBreached):
		filters["sla_breached"] = 1
	if _as_bool(escalatedOnly):
		filters["is_escalated"] = 1

	names = frappe.get_all(
		"SRM Incident",
		filters=filters,
		pluck="name",
		order_by="modified desc",
		limit_page_length=200,
	)

	rows = []
	for name in names:
		doc = frappe.get_doc("SRM Incident", name)
		payload = serialize_incident(doc, include_timeline=False)
		if ward and ward.lower() not in (payload.get("ward") or "").lower():
			continue
		if status and payload.get("status") != status:
			continue
		rows.append(payload)
	return rows


@frappe.whitelist()
def get_incident(name=None):
	"""Return one TrustLedger-shaped incident including timeline."""
	if not name:
		frappe.throw(_("name is required"))
	frappe.has_permission("SRM Incident", "read", throw=True)
	if not frappe.db.exists("SRM Incident", name):
		return None
	doc = frappe.get_doc("SRM Incident", name)
	return serialize_incident(doc, include_timeline=True)


@frappe.whitelist()
def list_evidence(incident=None):
	"""Return evidence stubs for an incident."""
	if not incident:
		frappe.throw(_("incident is required"))
	frappe.has_permission("SRM Incident", "read", throw=True)
	if not frappe.db.exists("SRM Incident", incident):
		return []

	doc = frappe.get_doc("SRM Incident", incident)
	out = []
	for row in doc.get("attachments") or []:
		serialized = serialize_evidence_row(row, incident)
		if serialized:
			out.append(serialized)
	return out
