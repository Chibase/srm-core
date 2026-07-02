# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from srm_core.services.impact import (
	OBSERVED_SEVERITY_ORDINALS,
	compute_weighted_score,
	score_to_band,
	severity_to_ordinal,
)
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area, ensure_impact_taxonomy


class TestImpactScoring(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = ensure_geographic_area(f"Score Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Impact Score Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Impact scoring test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def test_severity_mapping_correctness(self):
		self.assertEqual(severity_to_ordinal("Very Low"), 1)
		self.assertEqual(severity_to_ordinal("Low"), 2)
		self.assertEqual(severity_to_ordinal("Medium"), 3)
		self.assertEqual(severity_to_ordinal("High"), 4)
		self.assertEqual(severity_to_ordinal("Very High"), 5)
		self.assertIsNone(severity_to_ordinal("Extreme"))
		self.assertEqual(len(OBSERVED_SEVERITY_ORDINALS), 5)

	def test_weighted_score_math_with_mixed_weights(self):
		rows = [
			frappe._dict({"impact_taxonomy": "A", "observed_severity": "Very High"}),
			frappe._dict({"impact_taxonomy": "B", "observed_severity": "Very Low"}),
		]
		weights = {"A": 2.0, "B": 1.0}
		# (5*2 + 1*1) / (3*5) * 100 = 73.33
		self.assertEqual(compute_weighted_score(rows, weights), 73.33)

	def test_band_threshold_boundaries(self):
		self.assertEqual(score_to_band(24.99), "Low")
		self.assertEqual(score_to_band(25), "Moderate")
		self.assertEqual(score_to_band(49.99), "Moderate")
		self.assertEqual(score_to_band(50), "High")
		self.assertEqual(score_to_band(74.99), "High")
		self.assertEqual(score_to_band(75), "Critical")

	def test_incident_scoring_updates_when_rows_added_and_removed(self):
		taxonomy = ensure_impact_taxonomy(
			f"Score Taxonomy {random_string(6)}",
			default_weight=2.0,
		)
		doc = self._make_incident(
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "High"},
			]
		)
		doc.insert()
		self.assertEqual(doc.impact_score, 80.0)
		self.assertEqual(doc.impact_band, "Critical")
		self.assertTrue(doc.impact_scored_on)
		self.assertEqual(doc.impact_scored_by, frappe.session.user)

		doc.impact_assessments = []
		doc.save()
		doc.reload()
		self.assertEqual(doc.impact_score, 0.0)
		self.assertEqual(doc.impact_band, "Low")

	def test_zero_row_fallback_to_low_and_zero(self):
		doc = self._make_incident()
		doc.insert()
		self.assertEqual(doc.impact_score, 0.0)
		self.assertEqual(doc.impact_band, "Low")
		self.assertTrue(doc.impact_scored_on)

	def test_invalid_severity_rejection(self):
		taxonomy = ensure_impact_taxonomy(f"Invalid Severity Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Extreme"},
			]
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()
