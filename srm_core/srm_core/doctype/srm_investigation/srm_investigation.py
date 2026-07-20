# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from srm_core.services.statuses import (
	INCIDENT_OPEN,
	INCIDENT_UNDER_INVESTIGATION,
	INVESTIGATION_COMPLETION_STATUSES,
)


class SRMInvestigation(Document):
	def validate(self):
		self._validate_target_close_date()

	def before_update_after_submit(self):
		self._validate_target_close_date()

	def on_submit(self):
		incident = frappe.get_doc("SRM Incident", self.incident)
		if incident.status == INCIDENT_OPEN:
			incident.status = INCIDENT_UNDER_INVESTIGATION
			incident.save(ignore_permissions=True)

	def on_update_after_submit(self):
		previous = self.get_doc_before_save()
		if not previous:
			return

		if previous.status != self.status and self.status in INVESTIGATION_COMPLETION_STATUSES:
			self._add_incident_completion_comment()

	def _validate_target_close_date(self):
		if self.target_close_date and self.opened_on:
			if getdate(self.target_close_date) < getdate(self.opened_on):
				frappe.throw(_("Target close date cannot be earlier than opened on date."))

	def _add_incident_completion_comment(self):
		try:
			incident = frappe.get_doc("SRM Incident", self.incident)
			incident.add_comment(
				"Comment",
				_("Investigation {0} marked as {1}.").format(self.name, self.status),
			)
		except Exception:
			frappe.log_error(
				title=f"SRM Investigation comment failed for {self.name}",
				message=frappe.get_traceback(),
			)
