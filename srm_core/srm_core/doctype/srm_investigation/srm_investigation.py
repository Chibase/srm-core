# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class SRMInvestigation(Document):
	def validate(self):
		if self.target_close_date and self.opened_on:
			if getdate(self.target_close_date) < getdate(self.opened_on):
				frappe.throw(_("Target close date cannot be earlier than opened on date."))

