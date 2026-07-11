"""TrustLedger project API (whitelisted).

Until a Project Site DocType exists, projects are derived from distinct
`SRM Incident.project` values as temporary stubs.
"""

from __future__ import annotations

import frappe
from frappe import _

from srm_core.api.serializers import geographic_label, serialize_project_stub


@frappe.whitelist()
def list_projects(ward=None, status=None, contractorName=None):
	"""Return TrustLedger-shaped project stubs."""
	frappe.has_permission("SRM Incident", "read", throw=True)

	rows = frappe.get_all(
		"SRM Incident",
		fields=["name", "project", "programme", "geographic_area", "geographic_area_text"],
		filters={"project": ["is", "set"]},
		limit_page_length=500,
	)

	by_project: dict[str, dict] = {}
	for row in rows:
		key = (row.project or "").strip()
		if not key or key in by_project:
			continue
		sample = {
			"programme": row.programme,
			"ward": geographic_label(row),
		}
		stub = serialize_project_stub(key, sample)
		if ward and ward.lower() not in (stub.get("ward") or "").lower():
			continue
		if status and stub.get("status") != status:
			continue
		if contractorName and stub.get("contractorName") != contractorName:
			continue
		by_project[key] = stub

	return list(by_project.values())


@frappe.whitelist()
def get_project(name=None):
	"""Return one project stub by key."""
	if not name:
		frappe.throw(_("name is required"))
	frappe.has_permission("SRM Incident", "read", throw=True)

	rows = frappe.get_all(
		"SRM Incident",
		fields=["project", "programme", "geographic_area", "geographic_area_text"],
		filters={"project": name},
		limit_page_length=1,
	)
	if not rows:
		return None
	row = rows[0]
	return serialize_project_stub(
		name,
		{"programme": row.programme, "ward": geographic_label(row)},
	)
