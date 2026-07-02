"""Geographic Area helpers for SRM Core."""

import frappe
from frappe import _


def get_or_create_geographic_area(area_name):
	area_name = (area_name or "").strip()
	if not area_name:
		return None, False

	if frappe.db.exists("Geographic Area", area_name):
		return area_name, False

	doc = frappe.get_doc(
		{
			"doctype": "Geographic Area",
			"area_name": area_name,
			"active": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name, True


def validate_geographic_area_link(doc):
	if doc.geographic_area:
		return

	frappe.throw(
		_("Geographic Area is required. Select a linked geographic area."),
		title=_("Missing Geographic Area"),
	)
