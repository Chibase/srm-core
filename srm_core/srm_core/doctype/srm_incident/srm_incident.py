# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class SRMIncident(Document):
	def validate(self):
		if cint(self.iks_sensitive) and not cint(self.consent_obtained):
			frappe.throw(_("Consent must be obtained for IKS-sensitive incidents."))

		if (
			self.docstatus == 1
			and self.status in ("Resolved", "Closed")
			and not self.resolution_summary
		):
			frappe.throw(
				_("Resolution summary is required when status is Resolved or Closed.")
			)

