# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe


def ensure_geographic_area(name="Ward 12"):
	if not frappe.db.exists("Geographic Area", name):
		frappe.get_doc(
			{
				"doctype": "Geographic Area",
				"area_name": name,
				"active": 1,
			}
		).insert(ignore_permissions=True)
	return name


def ensure_impact_taxonomy(name="Community Trust", **overrides):
	if frappe.db.exists("SRM Impact Taxonomy", name):
		doc = frappe.get_doc("SRM Impact Taxonomy", name)
		for key, value in overrides.items():
			setattr(doc, key, value)
		if overrides:
			doc.save(ignore_permissions=True)
		return name

	data = {
		"doctype": "SRM Impact Taxonomy",
		"taxonomy_name": name,
		"impact_category": "Social",
		"default_weight": 1.0,
		"is_active": 1,
	}
	data.update(overrides)
	frappe.get_doc(data).insert(ignore_permissions=True)
	return name


def ensure_high_priority_assignment(doc, assignee="Administrator", task_title="Review incident"):
	"""Set owner and task row required for P1/P2 incident validation."""
	if not doc.get("incident_owner"):
		doc.incident_owner = assignee

	has_task = any(
		row.assignee and row.status in {"Open", "In Progress", "Blocked", "Done"}
		for row in (doc.investigation_tasks or [])
	)
	if not has_task:
		doc.append(
			"investigation_tasks",
			{
				"task_title": task_title,
				"assignee": assignee,
				"status": "Open",
				"priority": "Medium",
			},
		)
	return doc


def ensure_risk_register(name="Operational Risk", **overrides):
	if frappe.db.exists("SRM Risk Register", name):
		doc = frappe.get_doc("SRM Risk Register", name)
		for key, value in overrides.items():
			setattr(doc, key, value)
		if overrides:
			doc.save(ignore_permissions=True)
		return name

	data = {
		"doctype": "SRM Risk Register",
		"risk_title": name,
		"risk_status": "Open",
	}
	data.update(overrides)
	frappe.get_doc(data).insert(ignore_permissions=True)
	return name
