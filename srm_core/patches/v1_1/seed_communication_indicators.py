# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Seed example Impact Indicators for Communication Impact Phase 1.

Creates reference indicators that can be used in Communication Objectives.
"""

import frappe
from frappe import logger


SEED_INDICATORS = [
	{
		"indicator_name": "% Population Aware of Initiative",
		"indicator_type": "Percentage",
		"description": "Percentage of target population that is aware of the initiative",
		"measurement_unit": "%",
		"baseline_value": 0,
		"target_value": 100,
		"is_active": 1,
		"sort_order": 10,
	},
	{
		"indicator_name": "% Understanding Key Concepts",
		"indicator_type": "Percentage",
		"description": "Percentage of stakeholders who understand key concepts of the initiative",
		"measurement_unit": "%",
		"baseline_value": 0,
		"target_value": 100,
		"is_active": 1,
		"sort_order": 20,
	},
	{
		"indicator_name": "% Trust in Organization",
		"indicator_type": "Percentage",
		"description": "Percentage of stakeholders who trust the organization",
		"measurement_unit": "%",
		"baseline_value": 0,
		"target_value": 100,
		"is_active": 1,
		"sort_order": 30,
	},
	{
		"indicator_name": "% Program Participation",
		"indicator_type": "Percentage",
		"description": "Percentage of eligible population participating in the program",
		"measurement_unit": "%",
		"baseline_value": 0,
		"target_value": 100,
		"is_active": 1,
		"sort_order": 40,
	},
	{
		"indicator_name": "% Service Uptake",
		"indicator_type": "Percentage",
		"description": "Percentage of eligible population utilizing the service",
		"measurement_unit": "%",
		"baseline_value": 0,
		"target_value": 100,
		"is_active": 1,
		"sort_order": 50,
	},
]


def execute():
	"""
	Seed example Impact Indicators.
	"""
	for indicator_data in SEED_INDICATORS:
		if not frappe.db.exists("Impact Indicator", indicator_data["indicator_name"]):
			indicator = frappe.get_doc({
				"doctype": "Impact Indicator",
				**indicator_data
			})
			indicator.insert(ignore_permissions=True)
			logger().info(f"Seeded indicator: {indicator_data['indicator_name']}")
		else:
			logger().info(f"Indicator already exists: {indicator_data['indicator_name']}")
