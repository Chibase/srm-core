# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, flt, get_datetime, now_datetime

from srm_core.services.escalation import (
	ESCALATION_NONE,
	derive_escalation_level,
	resolve_escalation_reason,
	should_refresh_escalation_stamp,
	validate_high_priority_assignment,
)
from srm_core.services.geographic_area import validate_geographic_area_link
from srm_core.services.attachments import validate_incident_attachment_rows
from srm_core.services.comments import validate_incident_comment_rows
from srm_core.services.impact import (
	compute_weighted_score,
	score_to_band,
	validate_impact_assessment_rows,
)
from srm_core.services.investigation_tasks import (
	format_blocking_tasks_message,
	get_blocking_tasks,
	validate_investigation_task_rows,
)
from srm_core.services.risk_rollup import (
	apply_incident_risk_linkage,
	linked_risk_changed,
	touch_risk_register_with_incident,
	validate_residual_risk_close_gate,
)
from srm_core.services.permissions import user_has_iks_privileged_role, user_has_system_manager_role
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
from srm_core.services.timeline import (
	EVENT_STATUS_CHANGED,
	emit_incident_event,
	emit_timeline_events_for_incident,
	make_idempotency_key,
)


class SRMIncident(Document):
	def validate(self):
		self._run_incident_validations()

	def before_update_after_submit(self):
		self._run_incident_validations()

	def on_submit(self):
		previous_status = self.status
		if self.status == INCIDENT_DRAFT:
			self.status = INCIDENT_OPEN
			self.db_set("status", INCIDENT_OPEN)

		if not self.sla_due_date and not self.sla_due_by:
			self.sla_due_date = add_to_date(now_datetime(), hours=72)
			self.sla_due_by = self.sla_due_date
			self.db_set("sla_due_date", self.sla_due_date)
			self.db_set("sla_due_by", self.sla_due_by)

		self._persist_computed_fields()

		if previous_status != self.status:
			snapshot = {"previous_status": previous_status, "current_status": self.status}
			emit_incident_event(
				incident=self.name,
				event_type=EVENT_STATUS_CHANGED,
				summary=f"Status changed: {previous_status} -> {self.status}",
				details=snapshot,
				idempotency_key=make_idempotency_key(self.name, EVENT_STATUS_CHANGED, snapshot),
			)

	def after_insert(self):
		self._emit_timeline_events(is_insert=True)
		if self.linked_risk:
			touch_risk_register_with_incident(
				self.linked_risk,
				self.name,
				self.incident_title,
			)

	def on_update(self):
		previous = self.get_doc_before_save()
		self._emit_timeline_events(is_insert=False)
		if linked_risk_changed(previous, self):
			touch_risk_register_with_incident(
				self.linked_risk,
				self.name,
				self.incident_title,
			)

	def _run_incident_validations(self):
		validate_geographic_area_link(self)
		previous = self.get_doc_before_save()
		validate_impact_assessment_rows(self.impact_assessments)
		validate_investigation_task_rows(self.investigation_tasks)
		validate_incident_comment_rows(
			self.comments,
			previous.comments if previous else None,
		)
		validate_incident_attachment_rows(
			self.attachments,
			previous.attachments if previous else None,
			incident_status=self.status,
		)
		self._apply_impact_scoring()
		self._apply_priority_and_sla()

		if cint(self.iks_sensitive) and not cint(self.consent_obtained):
			frappe.throw(_("Consent must be obtained for IKS-sensitive incidents."))

		self._validate_iks_guardrails()
		self._validate_investigation_task_close_gate()

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

		self._apply_escalation()
		validate_high_priority_assignment(
			self.priority_level,
			self.incident_owner,
			self.investigation_tasks,
		)
		apply_incident_risk_linkage(self, previous)
		validate_residual_risk_close_gate(self, previous)

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

	def _apply_escalation(self):
		previous = self.get_doc_before_save()
		previous_level = previous.escalation_level if previous else None
		was_escalated = cint(previous.is_escalated) if previous else 0

		requires_exec = cint(self.requires_executive_attention)
		new_level = derive_escalation_level(
			self.priority_level,
			self.impact_band,
			requires_exec,
			cint(self.sla_breached),
		)
		is_escalated = cint(new_level != ESCALATION_NONE)

		self.escalation_level = new_level
		self.is_escalated = is_escalated

		if is_escalated and (
			not self.escalated_on
			or should_refresh_escalation_stamp(
				previous_level, new_level, was_escalated, is_escalated
			)
		):
			self.escalated_on = now_datetime()
			self.escalated_by = frappe.session.user

		self.escalation_reason = resolve_escalation_reason(
			self.escalation_reason,
			new_level,
			self.priority_level,
			cint(self.sla_breached),
			self.impact_band,
			requires_exec=requires_exec,
		)

		if self.name:
			self._persist_escalation()

	def _persist_escalation(self):
		self.db_set("is_escalated", self.is_escalated, update_modified=False)
		self.db_set("escalation_level", self.escalation_level, update_modified=False)
		self.db_set("escalated_on", self.escalated_on, update_modified=False)
		self.db_set("escalated_by", self.escalated_by, update_modified=False)
		self.db_set("escalation_reason", self.escalation_reason, update_modified=False)

	def _validate_investigation_task_close_gate(self):
		previous = self.get_doc_before_save()
		closing = self.status == INCIDENT_CLOSED and (
			self.is_new() or not previous or previous.status != INCIDENT_CLOSED
		)
		if not closing:
			return

		blocking = get_blocking_tasks(self.investigation_tasks)
		if blocking and not user_has_system_manager_role():
			frappe.throw(format_blocking_tasks_message(blocking))

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
		self._persist_escalation()

	def _emit_timeline_events(self, is_insert=False, previous=None):
		if previous is None and not is_insert:
			previous = self.get_doc_before_save()
		emit_timeline_events_for_incident(self, previous=previous, is_insert=is_insert)
