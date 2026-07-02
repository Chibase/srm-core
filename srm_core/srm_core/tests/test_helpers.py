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
