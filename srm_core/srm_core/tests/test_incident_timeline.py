# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from srm_core.services.investigation_tasks import TASK_STATUS_DONE, TASK_STATUS_OPEN
from srm_core.services.timeline import (
	EVENT_ESCALATION_CHANGED,
	EVENT_IMPACT_SCORED,
	EVENT_INCIDENT_CREATED,
	EVENT_PRIORITY_COMPUTED,
	EVENT_SLA_UPDATED,
	EVENT_STATUS_CHANGED,
	EVENT_TASK_ADDED,
	EVENT_TASK_STATUS_CHANGED,
	emit_incident_event,
	get_incident_timeline,
	make_idempotency_key,
)
from srm_core.srm_core.tests.test_helpers import (
	ensure_geographic_area,
	ensure_high_priority_assignment,
	ensure_impact_taxonomy,
)


class TestIncidentTimeline(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_incident(self, **overrides):
		area = ensure_geographic_area(f"Timeline Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Timeline Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Timeline test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _event_count(self, incident_name, event_type=None):
		filters = {"incident": incident_name}
		if event_type:
			filters["event_type"] = event_type
		return frappe.db.count("SRM Incident Event", filters)

	def test_event_creation_on_incident_insert(self):
		doc = self._make_incident()
		doc.insert()
		self.assertTrue(
			frappe.db.exists(
				"SRM Incident Event",
				{"incident": doc.name, "event_type": EVENT_INCIDENT_CREATED},
			)
		)
		self.assertGreater(self._event_count(doc.name, EVENT_IMPACT_SCORED), 0)
		self.assertGreater(self._event_count(doc.name, EVENT_PRIORITY_COMPUTED), 0)
		self.assertGreater(self._event_count(doc.name, EVENT_SLA_UPDATED), 0)

	def test_status_change_emits_one_event(self):
		doc = self._make_incident(status="Open")
		doc.insert()
		before = self._event_count(doc.name, EVENT_STATUS_CHANGED)

		doc.status = "Under Investigation"
		doc.save()
		self.assertEqual(self._event_count(doc.name, EVENT_STATUS_CHANGED), before + 1)

	def test_no_duplicate_events_on_no_op_save(self):
		doc = self._make_incident()
		doc.insert()
		before = self._event_count(doc.name)

		doc.save()
		doc.reload()
		doc.save()
		self.assertEqual(self._event_count(doc.name), before)

	def test_impact_priority_escalation_sla_events_include_payload(self):
		taxonomy = ensure_impact_taxonomy(f"Timeline Taxonomy {random_string(6)}")
		doc = self._make_incident()
		doc.insert()
		before_impact = self._event_count(doc.name, EVENT_IMPACT_SCORED)

		doc.append(
			"impact_assessments",
			{"impact_taxonomy": taxonomy, "observed_severity": "Medium"},
		)
		doc.save()

		impact_event = frappe.get_all(
			"SRM Incident Event",
			filters={"incident": doc.name, "event_type": EVENT_IMPACT_SCORED},
			fields=["details_json"],
			order_by="event_time desc",
			limit=1,
		)[0]
		payload = json.loads(impact_event.details_json)
		self.assertEqual(payload["impact_band"], "High")
		self.assertEqual(self._event_count(doc.name, EVENT_IMPACT_SCORED), before_impact + 1)
		self.assertGreater(self._event_count(doc.name, EVENT_PRIORITY_COMPUTED), 0)
		self.assertGreater(self._event_count(doc.name, EVENT_ESCALATION_CHANGED), 0)
		self.assertGreater(self._event_count(doc.name, EVENT_SLA_UPDATED), 0)

	def test_task_add_and_status_change_events(self):
		doc = self._make_incident()
		doc.insert()
		doc.append(
			"investigation_tasks",
			{
				"task_title": "Collect evidence",
				"assignee": "Administrator",
				"status": TASK_STATUS_OPEN,
			},
		)
		doc.save()
		self.assertEqual(self._event_count(doc.name, EVENT_TASK_ADDED), 1)

		doc.investigation_tasks[0].status = TASK_STATUS_DONE
		doc.save()
		self.assertEqual(self._event_count(doc.name, EVENT_TASK_STATUS_CHANGED), 1)

	def test_idempotency_guard_prevents_duplicates(self):
		doc = self._make_incident()
		doc.insert()
		snapshot = {"incident": doc.name, "status": doc.status}
		key = make_idempotency_key(doc.name, EVENT_INCIDENT_CREATED, snapshot)
		emit_incident_event(
			incident=doc.name,
			event_type=EVENT_INCIDENT_CREATED,
			summary="Duplicate should be ignored",
			details=snapshot,
			idempotency_key=key,
		)
		self.assertEqual(
			frappe.db.count(
				"SRM Incident Event",
				{"incident": doc.name, "event_type": EVENT_INCIDENT_CREATED},
			),
			1,
		)

	def test_get_incident_timeline_returns_ordered_events(self):
		doc = self._make_incident()
		doc.insert()
		doc.status = "Under Investigation"
		doc.save()
		timeline = get_incident_timeline(doc.name, limit=10)
		self.assertGreaterEqual(len(timeline), 2)
		self.assertEqual(timeline[0]["event_time"] >= timeline[-1]["event_time"], True)

	def test_backfill_creates_baseline_events_once(self):
		from srm_core.patches.v1_0.backfill_incident_timeline import execute as backfill_timeline

		doc = self._make_incident(incident_title="Backfill Timeline Incident")
		doc.insert()
		frappe.db.delete(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_INCIDENT_CREATED},
		)

		backfill_timeline()
		backfill_timeline()
		self.assertEqual(self._event_count(doc.name, EVENT_INCIDENT_CREATED), 1)
		self.assertGreaterEqual(self._event_count(doc.name, EVENT_STATUS_CHANGED), 1)

	def test_high_priority_incident_timeline_with_assignment(self):
		taxonomy = ensure_impact_taxonomy(f"Timeline P2 Taxonomy {random_string(6)}")
		doc = self._make_incident(
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Very High"},
			],
		)
		ensure_high_priority_assignment(doc)
		doc.insert()
		self.assertGreater(self._event_count(doc.name), 0)
