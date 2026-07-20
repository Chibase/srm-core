# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, random_string

from srm_core.patches.v1_0.backfill_incident_residual_risk import execute as backfill_residual_risk
from srm_core.services.escalation import ESCALATION_L3, ESCALATION_NONE
from srm_core.services.investigation_tasks import TASK_STATUS_CANCELLED, TASK_STATUS_DONE, TASK_STATUS_OPEN
from srm_core.services.notifications import (
	RULE_RESIDUAL_RISK_CRITICAL,
	RULE_RISK_LINKED,
	STATUS_SENT,
)
from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.risk_rollup import (
	RESIDUAL_BAND_CRITICAL,
	RESIDUAL_BAND_HIGH,
	RESIDUAL_BAND_LOW,
	RESIDUAL_BAND_MODERATE,
	band_residual_risk,
	compute_residual_risk_score,
	compute_task_completion_ratio,
)
from srm_core.services.timeline import EVENT_RESIDUAL_RISK_UPDATED, EVENT_RISK_LINKED
from srm_core.srm_core.tests.test_helpers import (
	ensure_geographic_area,
	ensure_high_priority_assignment,
	ensure_impact_taxonomy,
	ensure_risk_register,
)


class TestRiskRollup(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.lead_user = cls._ensure_user("srm-lead-risk@test.com", "SRM Lead")
		cls.admin_user = cls._ensure_user("srm-admin-risk@test.com", "SRM Admin")
		cls.case_manager_user = cls._ensure_user("srm-case-manager-risk@test.com", "SRM Case Manager")

	@classmethod
	def _ensure_user(cls, email, role):
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"roles": [{"role": role}],
				}
			)
			user.insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", email)
			if role not in frappe.get_roles(email):
				user.add_roles(role)
		return email

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = ensure_geographic_area(f"Risk Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Risk Rollup Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Risk rollup test incident",
			"incident_owner": self.lead_user,
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _high_residual_incident(self, risk_name=None):
		taxonomy = ensure_impact_taxonomy(
			f"Risk Taxonomy {random_string(6)}",
			default_weight=2.0,
		)
		risk_name = risk_name or ensure_risk_register(f"Risk {random_string(6)}")
		doc = self._make_incident(
			linked_risk=risk_name,
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Very High"},
			],
		)
		ensure_high_priority_assignment(doc)
		doc.insert()
		return doc, risk_name

	def test_compute_residual_risk_score_formula(self):
		# 35 + 35 + 18 + 10 = 98.00
		score = compute_residual_risk_score(100, 100, ESCALATION_L3, 0.0)
		self.assertEqual(score, 98.0)
		# 0 + 0 + 2 + 10 = 12.00
		score = compute_residual_risk_score(0, 0, ESCALATION_NONE, 0.0)
		self.assertEqual(score, 12.0)
		# All done tasks remove penalty: 17.5 + 17.5 + 2 + 0 = 37.00
		score = compute_residual_risk_score(50, 50, ESCALATION_NONE, 1.0)
		self.assertEqual(score, 37.0)

	def test_band_boundaries(self):
		self.assertEqual(band_residual_risk(24.99), RESIDUAL_BAND_LOW)
		self.assertEqual(band_residual_risk(25), RESIDUAL_BAND_MODERATE)
		self.assertEqual(band_residual_risk(49.99), RESIDUAL_BAND_MODERATE)
		self.assertEqual(band_residual_risk(50), RESIDUAL_BAND_HIGH)
		self.assertEqual(band_residual_risk(74.99), RESIDUAL_BAND_HIGH)
		self.assertEqual(band_residual_risk(75), RESIDUAL_BAND_CRITICAL)

	def test_no_task_completion_ratio_is_zero(self):
		self.assertEqual(compute_task_completion_ratio([]), 0.0)
		rows = [frappe._dict({"status": TASK_STATUS_CANCELLED})]
		self.assertEqual(compute_task_completion_ratio(rows), 0.0)

	def test_linked_risk_set_stamps_and_computes_residual(self):
		doc, risk_name = self._high_residual_incident()
		self.assertEqual(doc.linked_risk, risk_name)
		self.assertEqual(doc.risk_linked_by, "Administrator")
		self.assertTrue(doc.risk_linked_on)
		self.assertEqual(doc.residual_risk_band, RESIDUAL_BAND_CRITICAL)
		self.assertTrue(doc.residual_risk_score >= 75)
		self.assertTrue(doc.residual_risk_rationale)

	def test_linked_risk_clear_keeps_stamps_and_clears_residual(self):
		doc, _risk_name = self._high_residual_incident()
		linked_on = doc.risk_linked_on
		linked_by = doc.risk_linked_by

		doc.linked_risk = None
		doc.save()
		doc.reload()

		self.assertFalse(doc.linked_risk)
		self.assertEqual(doc.risk_linked_on, linked_on)
		self.assertEqual(doc.risk_linked_by, linked_by)
		self.assertEqual(flt(doc.residual_risk_score), 0)
		self.assertFalse(doc.residual_risk_band)
		self.assertFalse(doc.residual_risk_rationale)

	def _ready_to_close_incident(self, doc):
		for task in doc.investigation_tasks:
			task.status = TASK_STATUS_DONE
		doc.save()
		doc.submit()
		doc.status = "Resolved"
		doc.resolution_summary = "Resolved for closure test."
		doc.save()
		return doc

	def test_close_blocked_on_critical_residual_for_non_system_manager(self):
		doc, _risk_name = self._high_residual_incident()
		self._ready_to_close_incident(doc)

		frappe.set_user(self.case_manager_user)
		doc.reload()
		doc.status = "Closed"
		doc.resolution_summary = "Attempted close with critical residual risk."
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_system_manager_can_close_with_critical_residual(self):
		doc, _risk_name = self._high_residual_incident()
		doc.submit()
		doc.status = "Resolved"
		doc.resolution_summary = "Resolved."
		doc.save()

		frappe.set_user("Administrator")
		doc.reload()
		doc.status = "Closed"
		doc.resolution_summary = "Closed by System Manager override."
		doc.save()
		doc.reload()
		self.assertEqual(doc.status, "Closed")

	def test_risk_linked_timeline_event_emitted(self):
		doc, _risk_name = self._high_residual_incident()
		self.assertEqual(
			frappe.db.count(
				"SRM Incident Event",
				{"incident": doc.name, "event_type": EVENT_RISK_LINKED},
			),
			1,
		)

	def test_residual_risk_updated_timeline_event_on_material_change(self):
		doc, _risk_name = self._high_residual_incident()
		before = frappe.db.count(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_RESIDUAL_RISK_UPDATED},
		)
		self.assertGreaterEqual(before, 1)

		doc.append(
			"investigation_tasks",
			{
				"task_title": "Complete mitigation review",
				"assignee": "Administrator",
				"status": TASK_STATUS_DONE,
				"priority": "High",
			},
		)
		doc.save()
		after = frappe.db.count(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_RESIDUAL_RISK_UPDATED},
		)
		self.assertGreater(after, before)

	def test_risk_linked_notification(self):
		doc, _risk_name = self._high_residual_incident()
		self.assertTrue(
			frappe.db.exists(
				"SRM Notification",
				{
					"incident": doc.name,
					"recipient": self.lead_user,
					"rule_key": RULE_RISK_LINKED,
					"status": STATUS_SENT,
				},
			)
		)

	def test_critical_residual_notification(self):
		doc, _risk_name = self._high_residual_incident()
		self.assertTrue(
			frappe.db.exists(
				"SRM Notification",
				{
					"incident": doc.name,
					"recipient": self.admin_user,
					"rule_key": RULE_RESIDUAL_RISK_CRITICAL,
					"status": STATUS_SENT,
				},
			)
		)

	def test_risk_register_touchpoint_appends_reference(self):
		risk_name = ensure_risk_register(f"Touchpoint Risk {random_string(6)}")
		doc = self._make_incident(linked_risk=risk_name)
		doc.insert()
		references = frappe.db.get_value("SRM Risk Register", risk_name, "incident_references")
		self.assertIn(doc.name, references or "")

	def test_backfill_patch_is_idempotent(self):
		doc, _risk_name = self._high_residual_incident()
		frappe.db.set_value(
			"SRM Incident",
			doc.name,
			{
				"residual_risk_score": 0,
				"residual_risk_band": "",
				"residual_risk_rationale": "",
			},
			update_modified=False,
		)
		backfill_residual_risk()
		score_after_first = frappe.db.get_value("SRM Incident", doc.name, "residual_risk_score")
		band_after_first = frappe.db.get_value("SRM Incident", doc.name, "residual_risk_band")
		self.assertGreater(flt(score_after_first), 0)
		self.assertTrue(band_after_first)

		backfill_residual_risk()
		self.assertEqual(
			frappe.db.get_value("SRM Incident", doc.name, "residual_risk_score"),
			score_after_first,
		)
		self.assertEqual(
			frappe.db.get_value("SRM Incident", doc.name, "residual_risk_band"),
			band_after_first,
		)

	def test_task_completion_ratio_excludes_cancelled_tasks(self):
		rows = [
			frappe._dict({"status": TASK_STATUS_DONE}),
			frappe._dict({"status": TASK_STATUS_OPEN}),
			frappe._dict({"status": TASK_STATUS_CANCELLED}),
		]
		self.assertEqual(compute_task_completion_ratio(rows), 0.5)
