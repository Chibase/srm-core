# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from srm_core.api import ai as ai_api
from srm_core.api import engagements as engagements_api
from srm_core.api import incidents as incidents_api
from srm_core.api import projects as projects_api
from srm_core.api.serializers import map_incident_status, serialize_incident
from srm_core.srm_core.tests.test_helpers import (
	ensure_geographic_area,
	ensure_high_priority_assignment,
)


class TestTrustLedgerApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_geographic_area("TL API Ward")

	def _make_incident(self, **overrides):
		data = {
			"doctype": "SRM Incident",
			"incident_title": "TrustLedger API fixture",
			"incident_date": "2026-07-10",
			"incident_channel": "Community Forum",
			"geographic_area": "TL API Ward",
			"geographic_area_text": "TL API Ward",
			"severity": "Medium",
			"status": "Open",
			"description": "API packet test",
			"project": "Demo Corridor",
			"programme": "Demo Programme",
		}
		data.update(overrides)
		doc = frappe.get_doc(data)
		if doc.priority_level in ("P1-Critical", "P2-High") or data.get("priority_level") in (
			"P1-Critical",
			"P2-High",
		):
			ensure_high_priority_assignment(doc)
		return doc

	def test_status_mapping(self):
		self.assertEqual(map_incident_status({"status": "Draft", "is_escalated": 0}), "Open")
		self.assertEqual(map_incident_status({"status": "Open", "is_escalated": 0}), "Open")
		self.assertEqual(
			map_incident_status({"status": "Under Investigation", "is_escalated": 0}),
			"Investigating",
		)
		self.assertEqual(map_incident_status({"status": "Resolved", "is_escalated": 0}), "Closed")
		self.assertEqual(map_incident_status({"status": "Closed", "is_escalated": 0}), "Closed")
		self.assertEqual(map_incident_status({"status": "Open", "is_escalated": 1}), "Escalated")
		self.assertEqual(
			map_incident_status({"status": "Under Investigation", "is_escalated": 1}),
			"Escalated",
		)
		self.assertEqual(map_incident_status({"status": "Closed", "is_escalated": 1}), "Closed")

	def test_list_and_get_incident(self):
		doc = self._make_incident()
		doc.insert()

		listed = incidents_api.list_incidents(projectId="Demo Corridor")
		self.assertTrue(any(row["id"] == doc.name for row in listed))

		detail = incidents_api.get_incident(name=doc.name)
		self.assertEqual(detail["id"], doc.name)
		self.assertEqual(detail["status"], "Open")
		self.assertEqual(detail["projectId"], "Demo Corridor")
		self.assertIn("timeline", detail)
		self.assertIsInstance(detail["timeline"], list)

		projects = projects_api.list_projects()
		self.assertTrue(any(p["id"] == "Demo Corridor" for p in projects))

		notes = engagements_api.list_meeting_notes(projectId="Demo Corridor")
		self.assertEqual(notes, [])

	def test_list_evidence_skips_removed(self):
		doc = self._make_incident(incident_title="Evidence API fixture")
		doc.append(
			"attachments",
			{
				"file_name": "photo.jpg",
				"file_url": "/files/photo.jpg",
				"evidence_type": "screenshot",
				"classification": "internal",
				"is_primary_evidence": 1,
			},
		)
		doc.append(
			"attachments",
			{
				"file_name": "gone.pdf",
				"file_url": "/files/gone.pdf",
				"evidence_type": "document",
				"classification": "confidential",
			},
		)
		doc.insert()
		doc.attachments[1].is_removed = 1
		doc.attachments[1].removal_reason = "duplicate"
		doc.save()

		rows = incidents_api.list_evidence(incident=doc.name)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["fileName"], "photo.jpg")
		self.assertEqual(rows[0]["classification"], "General")
		self.assertTrue(rows[0]["isPrimary"])

	def test_ai_suggest_triage_shape(self):
		out = ai_api.suggest_triage(
			description="Safety near school — urgent hazard on the road trench",
			ward="TL API Ward",
		)
		self.assertEqual(out["suggestedPriority"], "P1-Critical")
		self.assertIn("Safety", out["category"])
		self.assertGreaterEqual(out["confidence"], 0)
		self.assertLessEqual(out["confidence"], 1)
		self.assertTrue(out["summary"])
		self.assertEqual(out["model"], "srm-heuristic-v0")
		self.assertEqual(out["promptVersion"], "srm-ai-v0")

	def test_serialize_incident_keys(self):
		doc = self._make_incident(incident_title="Serialize keys", project="Shape Project")
		doc.insert()
		row = serialize_incident(doc, include_timeline=True)
		for key in (
			"id",
			"title",
			"description",
			"ward",
			"geographicArea",
			"status",
			"priority",
			"projectId",
			"projectName",
			"reportedByRole",
			"reportedAt",
			"slaDueBy",
			"slaBreached",
			"escalationLevel",
			"ownerName",
			"category",
			"impactScore",
			"sentimentScore",
			"timeline",
		):
			self.assertIn(key, row)
		self.assertEqual(row["title"], "Serialize keys")
		self.assertEqual(row["projectId"], "Shape Project")
