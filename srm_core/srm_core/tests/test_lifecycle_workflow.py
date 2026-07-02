# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, get_datetime, now_datetime

from srm_core.services.statuses import (
	INCIDENT_OPEN,
	INCIDENT_UNDER_INVESTIGATION,
	INVESTIGATION_COMPLETED,
)


class TestLifecycleWorkflow(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Lifecycle Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area_text": "Ward 12",
			"severity": "Medium",
			"status": "Open",
			"description": "Lifecycle test description",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _make_investigation(self, incident_name, **overrides):
		data = {
			"doctype": "SRM Investigation",
			"incident": incident_name,
			"investigator": frappe.session.user,
			"opened_on": now_datetime(),
			"status": "Open",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def test_incident_submit_moves_draft_to_open(self):
		doc = self._make_incident(status="Draft")
		doc.insert()
		doc.submit()
		doc.reload()
		self.assertEqual(doc.status, INCIDENT_OPEN)

	def test_incident_submit_sets_default_sla_due_date_when_missing(self):
		doc = self._make_incident(status="Open")
		doc.insert()
		before_submit = now_datetime()
		doc.submit()
		doc.reload()
		self.assertTrue(doc.sla_due_date)
		sla_due = get_datetime(doc.sla_due_date)
		expected_min = add_to_date(before_submit, hours=72)
		self.assertGreaterEqual(sla_due, add_to_date(expected_min, minutes=-1))

	def test_incident_sla_breached_when_overdue_and_unresolved(self):
		doc = self._make_incident(status="Open")
		doc.sla_due_date = add_to_date(now_datetime(), hours=-1)
		doc.insert()
		doc.submit()
		doc.reload()
		self.assertEqual(doc.sla_breached, 1)

		doc.status = "Resolved"
		doc.resolution_summary = "Resolved after SLA breach."
		doc.save()
		doc.reload()
		self.assertEqual(doc.sla_breached, 0)

	def test_investigation_submit_moves_incident_open_to_under_investigation(self):
		incident = self._make_incident(status="Open")
		incident.insert()
		incident.submit()

		investigation = self._make_investigation(incident.name)
		investigation.insert()
		investigation.submit()

		incident.reload()
		self.assertEqual(incident.status, INCIDENT_UNDER_INVESTIGATION)

	def test_investigation_completed_adds_incident_comment(self):
		incident = self._make_incident(status="Open")
		incident.insert()
		incident.submit()

		investigation = self._make_investigation(incident.name)
		investigation.insert()
		investigation.submit()

		investigation.status = INVESTIGATION_COMPLETED
		investigation.save()

		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": "SRM Incident",
				"reference_name": incident.name,
				"comment_type": "Comment",
			},
			fields=["content"],
		)
		self.assertTrue(
			any(investigation.name in comment.content for comment in comments),
			"Expected investigation completion comment on incident timeline.",
		)

