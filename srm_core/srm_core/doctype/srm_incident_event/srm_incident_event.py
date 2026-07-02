# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from srm_core.services.permissions import user_has_system_manager_role


class SRMIncidentEvent(Document):
	def before_insert(self):
		if frappe.flags.in_install or frappe.flags.in_patch:
			return
		if user_has_system_manager_role():
			return
		if frappe.session.user == "Administrator":
			return
		frappe.throw(_("Incident timeline events can only be created by system processes."))

	def before_update(self):
		frappe.throw(_("Incident timeline events are append-only and cannot be modified."))

	def on_trash(self):
		if not user_has_system_manager_role():
			frappe.throw(_("Incident timeline events cannot be deleted."))
