# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

from frappe.utils.nestedset import NestedSet


class GeographicArea(NestedSet):
	nsm_parent_field = "parent_geographic_area"
