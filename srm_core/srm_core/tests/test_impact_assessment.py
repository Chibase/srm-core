# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from srm_core.services.impact import severity_to_ordinal
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area, ensure_impact_taxonomy


class TestImpactAssessment(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = ensure_geographic_area(f"Impact Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Impact Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Impact assessment test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def test_taxonomy_creation_and_active_flag(self):
		name = f"Active Taxonomy {random_string(6)}"
		ensure_impact_taxonomy(name, is_active=1)
		self.assertTrue(frappe.db.get_value("SRM Impact Taxonomy", name, "is_active"))

		inactive_name = f"Inactive Taxonomy {random_string(6)}"
		ensure_impact_taxonomy(inactive_name, is_active=0)

		doc = self._make_incident(
			impact_assessments=[
				{
					"impact_taxonomy": inactive_name,
					"observed_severity": "Medium",
				}
			]
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_impact_assessment_creation_linked_to_incident(self):
		taxonomy = ensure_impact_taxonomy(f"Linked Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{
					"impact_taxonomy": taxonomy,
					"observed_severity": "High",
					"confidence_level": "Medium",
					"rationale": "Observed community concern.",
				}
			]
		)
		doc.insert()
		self.assertEqual(len(doc.impact_assessments), 1)
		self.assertEqual(doc.impact_assessments[0].impact_taxonomy, taxonomy)
		self.assertEqual(severity_to_ordinal("High"), 4)

	def test_duplicate_taxonomy_for_same_incident_rejected(self):
		taxonomy = ensure_impact_taxonomy(f"Duplicate Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Low"},
				{"impact_taxonomy": taxonomy, "observed_severity": "High"},
			]
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_required_fields_validation_on_impact_rows(self):
		taxonomy = ensure_impact_taxonomy(f"Required Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{
					"impact_taxonomy": taxonomy,
					"observed_severity": "",
				}
			]
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_seed_patch_creates_default_taxonomies_idempotently(self):
		from srm_core.patches.v1_0.seed_default_impact_taxonomy import execute as seed_taxonomies

		seed_taxonomies()
		seed_taxonomies()

		for name in (
			"Community Trust",
			"Regulatory Exposure",
			"Service Continuity",
			"Financial Exposure",
		):
			self.assertTrue(frappe.db.exists("SRM Impact Taxonomy", name))
