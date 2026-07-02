# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, get_datetime, now_datetime

from srm_core.services.permissions import user_has_iks_privileged_role
from srm_core.services.statuses import (
	INCIDENT_CLOSED,
	INCIDENT_DRAFT,
	INCIDENT_OPEN,
	INCIDENT_RESOLUTION_REQUIRED_STATUSES,
	INCIDENT_TERMINAL_STATUSES,
)


class SRMIncident(Document):
	def validate(self):
		self._run_incident_validations()

	def before_update_after_submit(self):
		self._run_incident_validations()

	def on_submit(self):
		if self.status == INCIDENT_DRAFT:
			self.status = INCIDENT_OPEN
			self.db_set("status", INCIDENT_OPEN)

		if not self.sla_due_date:
			self.sla_due_date = add_to_date(now_datetime(), hours=72)
			self.db_set("sla_due_date", self.sla_due_date)

		self._persist_computed_fields()

	def _run_incident_validations(self):
		if cint(self.iks_sensitive) and not cint(self.consent_obtained):
			frappe.throw(_("Consent must be obtained for IKS-sensitive incidents."))

		self._validate_iks_guardrails()

		if self.status in INCIDENT_RESOLUTION_REQUIRED_STATUSES and not self.resolution_summary:
			frappe.throw(
				_("Resolution summary is required when status is Resolved or Closed.")
			)

		if self.status == INCIDENT_CLOSED:
			if not self.closed_on:
				self.closed_on = now_datetime()
		else:
			self.closed_on = None

		self.sla_breached = cint(
			bool(
				self.sla_due_date
				and now_datetime() > get_datetime(self.sla_due_date)
				and self.status not in INCIDENT_TERMINAL_STATUSES
			)
		)

		if self.name and not self.is_new() and self.docstatus == 1:
			self._persist_computed_fields()

	def _validate_iks_guardrails(self):
		if not cint(self.iks_sensitive):
			return

		previous = self.get_doc_before_save()
		closing = self.status == INCIDENT_CLOSED and (
			self.is_new() or not previous or previous.status != INCIDENT_CLOSED
		)
		if closing and not user_has_iks_privileged_role():
			frappe.throw(
				_("Only SRM Admin or System Manager can close IKS-sensitive incidents.")
			)

		if self.docstatus == 1 and self.has_value_changed("resolution_summary"):
			if not user_has_iks_privileged_role():
				frappe.throw(
					_(
						"Only SRM Admin or System Manager can edit resolution summary on "
						"IKS-sensitive incidents after submission."
					)
				)
			self._apply_iks_audit_trail()

		if (
			self.docstatus == 1
			and self.has_value_changed("status")
			and user_has_iks_privileged_role()
		):
			self._apply_iks_audit_trail()

	def _apply_iks_audit_trail(self):
		self.last_sensitive_action_by = frappe.session.user
		self.last_sensitive_action_on = now_datetime()
		if self.name:
			self.db_set("last_sensitive_action_by", self.last_sensitive_action_by, update_modified=False)
			self.db_set("last_sensitive_action_on", self.last_sensitive_action_on, update_modified=False)

	def _persist_computed_fields(self):
		self.db_set("sla_breached", self.sla_breached, update_modified=False)
		self.db_set("closed_on", self.closed_on, update_modified=False)
