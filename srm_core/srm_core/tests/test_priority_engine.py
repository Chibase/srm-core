# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, get_datetime, now_datetime, random_string

from srm_core.services.priority import (
	PRIORITY_P1_CRITICAL,
	PRIORITY_P2_HIGH,
	PRIORITY_P3_MEDIUM,
	PRIORITY_P4_LOW,
	compute_priority_score,
	normalize_sentiment_intensity,
	priority_band,
	sla_hours_for_priority,
)
from srm_core.srm_core.tests.test_helpers import (
	ensure_geographic_area,
	ensure_high_priority_assignment,
	ensure_impact_taxonomy,
)


class TestPriorityEngine(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = overrides.pop("geographic_area", None) or ensure_geographic_area(
			f"Priority Ward {random_string(6)}"
		)
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Priority Engine Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Priority engine test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _make_sentiment(self, geographic_area, sentiment_score, linked_incident=None):
		return frappe.get_doc(
			{
				"doctype": "SRM Sentiment Capture",
				"capture_date": "2026-07-02",
				"geographic_area": geographic_area,
				"geographic_area_text": geographic_area,
				"stakeholder_group": "Community",
				"source_type": "Survey",
				"sentiment_score": sentiment_score,
				"linked_incident": linked_incident,
			}
		).insert(ignore_permissions=True)

	def test_priority_band_boundaries(self):
		self.assertEqual(priority_band(24.99), PRIORITY_P4_LOW)
		self.assertEqual(priority_band(25), PRIORITY_P3_MEDIUM)
		self.assertEqual(priority_band(49.99), PRIORITY_P3_MEDIUM)
		self.assertEqual(priority_band(50), PRIORITY_P2_HIGH)
		self.assertEqual(priority_band(74.99), PRIORITY_P2_HIGH)
		self.assertEqual(priority_band(75), PRIORITY_P1_CRITICAL)

	def test_zero_impact_zero_sentiment_p4_and_72h(self):
		doc = self._make_incident()
		before = now_datetime()
		doc.insert()
		doc.reload()
		self.assertEqual(doc.priority_score, 0.0)
		self.assertEqual(doc.priority_level, PRIORITY_P4_LOW)
		self.assertEqual(doc.sla_target_hours, 72.0)
		self.assertTrue(doc.sla_due_by)
		sla_due = get_datetime(doc.sla_due_by)
		creation = get_datetime(doc.creation)
		expected = add_to_date(creation, hours=72)
		self.assertGreaterEqual(sla_due, add_to_date(expected, minutes=-1))
		self.assertLessEqual(sla_due, add_to_date(before, hours=72, minutes=1))

	def test_high_impact_high_sentiment_p1_and_4h(self):
		area = ensure_geographic_area(f"Priority High Ward {random_string(6)}")
		taxonomy = ensure_impact_taxonomy(
			f"Priority Taxonomy {random_string(6)}",
			default_weight=1.0,
		)
		doc = self._make_incident(
			geographic_area=area,
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Very High"},
			],
		)
		ensure_high_priority_assignment(doc)
		doc.insert()
		self._make_sentiment(area, -100, linked_incident=doc.name)
		doc.save()
		doc.reload()
		self.assertEqual(doc.impact_score, 100.0)
		self.assertEqual(doc.priority_score, 100.0)
		self.assertEqual(doc.priority_level, PRIORITY_P1_CRITICAL)
		self.assertEqual(doc.sla_target_hours, 4.0)

	def test_sla_due_recomputes_when_priority_escalates_pre_closure(self):
		area = ensure_geographic_area(f"Priority Escalation Ward {random_string(6)}")
		taxonomy = ensure_impact_taxonomy(
			f"Escalation Taxonomy {random_string(6)}",
			default_weight=1.0,
		)
		doc = self._make_incident(geographic_area=area)
		doc.insert()
		doc.reload()
		initial_due = get_datetime(doc.sla_due_by)
		self.assertEqual(doc.priority_level, PRIORITY_P4_LOW)

		doc.impact_assessments = []
		doc.append(
			"impact_assessments",
			{"impact_taxonomy": taxonomy, "observed_severity": "Very High"},
		)
		ensure_high_priority_assignment(doc)
		before_escalation = now_datetime()
		doc.save()
		doc.reload()
		self.assertEqual(doc.priority_level, PRIORITY_P2_HIGH)
		self.assertEqual(doc.sla_target_hours, 12.0)
		new_due = get_datetime(doc.sla_due_by)
		expected_min = add_to_date(before_escalation, hours=12, minutes=-1)
		self.assertGreaterEqual(new_due, expected_min)
		self.assertLess(new_due, initial_due)

	def test_closed_incident_does_not_shift_sla_due_on_save(self):
		doc = self._make_incident(status="Open")
		doc.insert()
		doc.submit()
		doc.status = "Resolved"
		doc.resolution_summary = "Resolved for closure test."
		doc.save()
		doc.status = "Closed"
		doc.resolution_summary = "Closed for SLA freeze test."
		doc.save()
		doc.reload()
		frozen_due = doc.sla_due_by

		ensure_high_priority_assignment(doc)
		doc.append(
			"impact_assessments",
			{
				"impact_taxonomy": ensure_impact_taxonomy(f"Closed SLA Taxonomy {random_string(6)}"),
				"observed_severity": "Very High",
			},
		)
		doc.save()
		doc.reload()
		self.assertEqual(get_datetime(doc.sla_due_by), get_datetime(frozen_due))

	def test_deterministic_priority_computation(self):
		self.assertEqual(normalize_sentiment_intensity(-50), 15.0)
		self.assertEqual(normalize_sentiment_intensity(50), 15.0)
		self.assertEqual(compute_priority_score(80, 100), 86.0)
		self.assertEqual(compute_priority_score(100, 100), 100.0)
		self.assertEqual(compute_priority_score(0, 0), 0.0)
		self.assertEqual(compute_priority_score(50, 50), 50.0)
		self.assertEqual(sla_hours_for_priority(PRIORITY_P2_HIGH), 12.0)
