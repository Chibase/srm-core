# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, flt, get_datetime, now_datetime

from srm_core.services.geographic_area import validate_geographic_area_link
from srm_core.services.impact import (
	compute_weighted_score,
	score_to_band,
	validate_impact_assessment_rows,
)
from srm_core.services.permissions import user_has_iks_privileged_role
from srm_core.services.priority import (
	compute_priority_score,
	priority_band,
	resolve_sentiment_signal,
	sla_hours_for_priority,
)
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

		if not self.sla_due_date and not self.sla_due_by:
			self.sla_due_date = add_to_date(now_datetime(), hours=72)
			self.sla_due_by = self.sla_due_date
			self.db_set("sla_due_date", self.sla_due_date)
			self.db_set("sla_due_by", self.sla_due_by)

		self._persist_computed_fields()

	def _run_incident_validations(self):
		validate_geographic_area_link(self)
		validate_impact_assessment_rows(self.impact_assessments)
		self._apply_impact_scoring()
		self._apply_priority_and_sla()

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
				(self.sla_due_by or self.sla_due_date)
				and now_datetime() > get_datetime(self.sla_due_by or self.sla_due_date)
				and self.status not in INCIDENT_TERMINAL_STATUSES
			)
		)

		if self.name and not self.is_new() and self.docstatus == 1:
			self._persist_computed_fields()

	def _apply_impact_scoring(self):
		if self.impact_assessments:
			self.impact_score = compute_weighted_score(self.impact_assessments)
		else:
			self.impact_score = 0.0

		self.impact_band = score_to_band(self.impact_score)
		self.impact_scored_on = now_datetime()
		self.impact_scored_by = frappe.session.user

		if self.name:
			self._persist_impact_score()

	def _persist_impact_score(self):
		self.db_set("impact_score", self.impact_score, update_modified=False)
		self.db_set("impact_band", self.impact_band, update_modified=False)
		self.db_set("impact_scored_on", self.impact_scored_on, update_modified=False)
		self.db_set("impact_scored_by", self.impact_scored_by, update_modified=False)

	def _apply_priority_and_sla(self):
		previous = self.get_doc_before_save()
		previous_level = previous.priority_level if previous else None

		sentiment_signal = resolve_sentiment_signal(
			self.name,
			self.geographic_area,
			reference_datetime=self.creation or now_datetime(),
		)
		self.priority_score = compute_priority_score(flt(self.impact_score), sentiment_signal)
		self.priority_level = priority_band(self.priority_score)
		self.priority_computed_on = now_datetime()
		self.priority_computed_by = frappe.session.user

		if self.status != INCIDENT_CLOSED:
			self.sla_target_hours = sla_hours_for_priority(self.priority_level)
			sla_hours = self.sla_target_hours
			base = get_datetime(self.creation or now_datetime())

			if not self.sla_due_by:
				self.sla_due_by = add_to_date(base, hours=sla_hours)
			elif previous_level and previous_level != self.priority_level:
				self.sla_due_by = add_to_date(now_datetime(), hours=sla_hours)

			self.sla_due_date = self.sla_due_by

		if self.name:
			self._persist_priority_and_sla()

	def _persist_priority_and_sla(self):
		self.db_set("priority_score", self.priority_score, update_modified=False)
		self.db_set("priority_level", self.priority_level, update_modified=False)
		self.db_set("priority_computed_on", self.priority_computed_on, update_modified=False)
		self.db_set("priority_computed_by", self.priority_computed_by, update_modified=False)
		if self.status != INCIDENT_CLOSED:
			self.db_set("sla_target_hours", self.sla_target_hours, update_modified=False)
			self.db_set("sla_due_by", self.sla_due_by, update_modified=False)
			self.db_set("sla_due_date", self.sla_due_date, update_modified=False)

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
		self._persist_priority_and_sla()
