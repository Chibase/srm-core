# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime, random_string

from srm_core.services.escalation import (
	AUTO_REASON_PREFIX,
	ESCALATION_L1,
	ESCALATION_L2,
	ESCALATION_L3,
	ESCALATION_NONE,
	build_auto_escalation_reason,
	derive_escalation_level,
	is_auto_escalation_reason,
	resolve_escalation_reason,
)
from srm_core.services.investigation_tasks import TASK_STATUS_OPEN
from srm_core.services.priority import PRIORITY_P2_HIGH, PRIORITY_P3_MEDIUM, PRIORITY_P4_LOW
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area, ensure_impact_taxonomy


class TestEscalationRules(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = ensure_geographic_area(f"Escalation Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Escalation Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Escalation test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _task_row(self, assignee="Administrator", **overrides):
		data = {
			"task_title": "Review evidence",
			"assignee": assignee,
			"status": TASK_STATUS_OPEN,
		}
		data.update(overrides)
		return data

	def test_escalation_level_triggers(self):
		self.assertEqual(
			derive_escalation_level("P4-Low", "Low", False, False),
			ESCALATION_NONE,
		)
		self.assertEqual(
			derive_escalation_level(PRIORITY_P3_MEDIUM, "Low", False, False),
			ESCALATION_L1,
		)
		self.assertEqual(
			derive_escalation_level(PRIORITY_P2_HIGH, "Low", False, False),
			ESCALATION_L2,
		)
		self.assertEqual(
			derive_escalation_level(PRIORITY_P4_LOW, "Low", False, True),
			ESCALATION_L2,
		)
		self.assertEqual(
			derive_escalation_level("P1-Critical", "Low", False, False),
			ESCALATION_L3,
		)
		self.assertEqual(
			derive_escalation_level(PRIORITY_P4_LOW, "Critical", False, False),
			ESCALATION_L3,
		)
		self.assertEqual(
			derive_escalation_level(PRIORITY_P4_LOW, "Low", True, False),
			ESCALATION_L3,
		)

	def test_escalation_precedence_l3_overrides_l2_and_l1(self):
		level = derive_escalation_level("P1-Critical", "Critical", False, True)
		self.assertEqual(level, ESCALATION_L3)

	def test_auto_reason_generation_and_manual_preservation(self):
		auto = build_auto_escalation_reason(
			ESCALATION_L2,
			PRIORITY_P2_HIGH,
			False,
			"Low",
		)
		self.assertTrue(is_auto_escalation_reason(auto))
		self.assertIn("P2-High", auto)

		manual = "Executive requested immediate review."
		resolved = resolve_escalation_reason(
			manual,
			ESCALATION_L2,
			PRIORITY_P2_HIGH,
			False,
			"Low",
		)
		self.assertEqual(resolved, manual)

	def test_auto_reason_cleared_on_de_escalation(self):
		auto = build_auto_escalation_reason(
			ESCALATION_L1,
			PRIORITY_P3_MEDIUM,
			False,
			"Low",
		)
		cleared = resolve_escalation_reason(auto, ESCALATION_NONE, PRIORITY_P3_MEDIUM, False, "Low")
		self.assertIsNone(cleared)

		manual = "Manual note retained."
		kept = resolve_escalation_reason(manual, ESCALATION_NONE, PRIORITY_P4_LOW, False, "Low")
		self.assertEqual(kept, manual)

	def test_escalation_timestamp_stamping_on_first_escalate_and_increase(self):
		taxonomy = ensure_impact_taxonomy(f"Stamp Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Medium"},
			],
		)
		before = now_datetime()
		doc.insert()
		self.assertEqual(doc.escalation_level, ESCALATION_L1)
		self.assertEqual(doc.is_escalated, 1)
		self.assertTrue(doc.escalated_on)
		first_stamp = doc.escalated_on

		tax_high = ensure_impact_taxonomy(
			f"Stamp High Taxonomy {random_string(6)}",
			default_weight=2.0,
		)
		tax_low = ensure_impact_taxonomy(
			f"Stamp Low Taxonomy {random_string(6)}",
			default_weight=1.0,
		)
		doc.incident_owner = "Administrator"
		doc.append("investigation_tasks", self._task_row())
		doc.impact_assessments = []
		doc.append(
			"impact_assessments",
			{"impact_taxonomy": tax_high, "observed_severity": "Very High"},
		)
		doc.append(
			"impact_assessments",
			{"impact_taxonomy": tax_low, "observed_severity": "Very Low"},
		)
		doc.save()
		self.assertEqual(doc.escalation_level, ESCALATION_L2)
		self.assertGreaterEqual(
			frappe.utils.get_datetime(doc.escalated_on),
			frappe.utils.get_datetime(first_stamp),
		)
		self.assertGreaterEqual(frappe.utils.get_datetime(doc.escalated_on), add_to_date(before, seconds=-5))

	def test_de_escalation_keeps_historical_stamp(self):
		taxonomy = ensure_impact_taxonomy(f"Deescalate Taxonomy {random_string(6)}")
		doc = self._make_incident(
			incident_owner="Administrator",
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "High"},
			],
		)
		doc.append("investigation_tasks", self._task_row())
		doc.insert()
		historical_on = doc.escalated_on
		historical_by = doc.escalated_by

		doc.impact_assessments = []
		doc.save()
		self.assertEqual(doc.escalation_level, ESCALATION_NONE)
		self.assertEqual(doc.is_escalated, 0)
		self.assertEqual(doc.escalated_on, historical_on)
		self.assertEqual(doc.escalated_by, historical_by)
		self.assertIsNone(doc.escalation_reason)

	def test_assignment_enforcement_for_p1_and_p2(self):
		taxonomy = ensure_impact_taxonomy(f"P2 Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Very High"},
			],
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

		doc.incident_owner = "Administrator"
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

		doc.append("investigation_tasks", self._task_row())
		doc.insert()
		self.assertEqual(doc.priority_level, PRIORITY_P2_HIGH)
		self.assertEqual(doc.escalation_level, ESCALATION_L3)

	def test_no_assignment_enforcement_for_p3_p4(self):
		doc = self._make_incident()
		doc.insert()
		self.assertEqual(doc.priority_level, PRIORITY_P4_LOW)
		self.assertFalse(doc.incident_owner)

		taxonomy = ensure_impact_taxonomy(f"P3 Taxonomy {random_string(6)}")
		doc.append(
			"impact_assessments",
			{"impact_taxonomy": taxonomy, "observed_severity": "Medium"},
		)
		doc.save()
		self.assertEqual(doc.priority_level, PRIORITY_P3_MEDIUM)
		self.assertEqual(doc.escalation_level, ESCALATION_L1)

	def test_sla_breach_auto_escalates_to_l2_with_reason(self):
		doc = self._make_incident()
		doc.insert()
		doc.sla_due_by = add_to_date(now_datetime(), hours=-1)
		doc.sla_due_date = doc.sla_due_by
		doc.save()
		doc.reload()
		self.assertEqual(doc.escalation_level, ESCALATION_L2)
		self.assertTrue(doc.escalation_reason.startswith(AUTO_REASON_PREFIX))
		self.assertIn("SLA breach", doc.escalation_reason)

	def test_requires_executive_attention_triggers_l3(self):
		doc = self._make_incident(requires_executive_attention=1)
		doc.insert()
		self.assertEqual(doc.escalation_level, ESCALATION_L3)
		self.assertIn("executive attention required", doc.escalation_reason)
