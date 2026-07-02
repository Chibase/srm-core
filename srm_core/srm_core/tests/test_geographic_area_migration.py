# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from srm_core.patches.v1_0.migrate_geographic_area_links import execute as migrate_geographic_area_links
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area


class TestGeographicAreaMigration(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _insert_legacy_incident(self, area_text):
		doc = frappe.get_doc(
			{
				"doctype": "SRM Incident",
				"incident_title": f"Legacy Incident {area_text}",
				"incident_date": "2026-07-02",
				"incident_channel": "Phone",
				"geographic_area_text": area_text,
				"severity": "Medium",
				"status": "Open",
				"description": "Legacy incident for migration test",
			}
		)
		doc.db_insert()
		return doc

	def _insert_legacy_sentiment(self, area_text):
		doc = frappe.get_doc(
			{
				"doctype": "SRM Sentiment Capture",
				"capture_date": "2026-07-02",
				"geographic_area_text": area_text,
				"stakeholder_group": "Community Group",
				"source_type": "Survey",
				"sentiment_score": 10,
			}
		)
		doc.db_insert()
		return doc

	def test_patch_creates_geographic_area_from_legacy_text(self):
		area_text = f"Patch Create Ward {random_string(8)}"
		self._insert_legacy_incident(area_text)
		self.assertFalse(frappe.db.exists("Geographic Area", area_text))

		migrate_geographic_area_links()

		self.assertTrue(frappe.db.exists("Geographic Area", area_text))

	def test_patch_backfills_incident_geographic_area(self):
		doc = self._insert_legacy_incident("Patch Incident Ward")
		migrate_geographic_area_links()
		self.assertEqual(
			frappe.db.get_value("SRM Incident", doc.name, "geographic_area"),
			"Patch Incident Ward",
		)

	def test_patch_backfills_sentiment_geographic_area(self):
		doc = self._insert_legacy_sentiment("Patch Sentiment Ward")
		migrate_geographic_area_links()
		self.assertEqual(
			frappe.db.get_value("SRM Sentiment Capture", doc.name, "geographic_area"),
			"Patch Sentiment Ward",
		)

	def test_patch_is_idempotent_on_rerun(self):
		doc = self._insert_legacy_incident("Patch Idempotent Ward")
		migrate_geographic_area_links()
		migrate_geographic_area_links()
		self.assertEqual(
			frappe.db.get_value("SRM Incident", doc.name, "geographic_area"),
			"Patch Idempotent Ward",
		)
		self.assertEqual(
			frappe.db.count("Geographic Area", {"area_name": "Patch Idempotent Ward"}),
			1,
		)

	def test_new_incident_requires_geographic_area_link(self):
		ensure_geographic_area("Unused Ward")
		doc = frappe.get_doc(
			{
				"doctype": "SRM Incident",
				"incident_title": "Missing Area Incident",
				"incident_date": "2026-07-02",
				"incident_channel": "Phone",
				"geographic_area_text": "Legacy only",
				"severity": "Medium",
				"status": "Open",
				"description": "Missing linked area",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_new_sentiment_requires_geographic_area_link(self):
		doc = frappe.get_doc(
			{
				"doctype": "SRM Sentiment Capture",
				"capture_date": "2026-07-02",
				"geographic_area_text": "Legacy only",
				"stakeholder_group": "Community Group",
				"source_type": "Survey",
				"sentiment_score": 5,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()
