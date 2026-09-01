# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Phase 1 Migration Patches
"""

import frappe
from frappe import logger


def execute():
	"""
	Create SRM roles required for Communication Impact framework.
	"""
	roles_config = [
		{
			"role_name": "SRM Admin",
			"description": "SRM Administrator - Full access to SRM features"
		},
		{
			"role_name": "SRM Analyst",
			"description": "SRM Analyst - Create and manage incidents, analysis"
		},
		{
			"role_name": "SRM Lead",
			"description": "SRM Lead - View and supervise SRM activities"
		},
		{
			"role_name": "SRM Viewer",
			"description": "SRM Viewer - Read-only access to SRM data"
		},
	]

	for role_config in roles_config:
		if not frappe.db.exists("Role", role_config["role_name"]):
			role = frappe.get_doc({
				"doctype": "Role",
				"role_name": role_config["role_name"],
				"disabled": 0,
			})
			role.insert(ignore_permissions=True)
			logger().info(f"Created role: {role_config['role_name']}")
		else:
			logger().info(f"Role already exists: {role_config['role_name']}")
