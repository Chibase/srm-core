# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from srm_core.srm_core.tests.test_helpers import ensure_geographic_area


class TestCoreDoctypes(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = overrides.pop("geographic_area", None) or ensure_geographic_area(
			overrides.pop("geographic_area_text", "Ward 12")
		)
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Test description",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def test_incident_fails_when_iks_sensitive_without_consent(self):
		doc = self._make_incident(iks_sensitive=1, consent_obtained=0)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_incident_resolved_requires_resolution_summary_after_submit(self):
		doc = self._make_incident(status="Open")
		doc.insert()
		doc.submit()
		doc.status = "Resolved"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_investigation_target_close_date_before_opened_on_fails(self):
		incident = self._make_incident()
		incident.insert()

		investigation = frappe.get_doc(
			{
				"doctype": "SRM Investigation",
				"incident": incident.name,
				"investigator": frappe.session.user,
				"opened_on": "2026-07-10 10:00:00",
				"target_close_date": "2026-07-05",
				"status": "Open",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			investigation.insert()

