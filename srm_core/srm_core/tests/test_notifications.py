# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime, random_string

from srm_core.services.investigation_tasks import TASK_STATUS_OPEN
from srm_core.services.notifications import (
	CHANNEL_EMAIL,
	CHANNEL_IN_APP,
	RULE_ESCALATION_L2_L3,
	RULE_PRIORITY_P1,
	RULE_SLA_DUE_6H,
	RULE_STATUS_CLOSED,
	STATUS_FAILED,
	STATUS_QUEUED,
	STATUS_SENT,
	dispatch_queued_notifications,
	evaluate_incident_event_for_notifications,
	get_unread_in_app_notifications,
	mark_notification_read,
	process_notifications_for_event,
	queue_notifications,
)
from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.timeline import (
	EVENT_ESCALATION_CHANGED,
	EVENT_PRIORITY_COMPUTED,
	EVENT_SLA_UPDATED,
	EVENT_STATUS_CHANGED,
	emit_incident_event,
)
from srm_core.srm_core.tests.test_helpers import (
	ensure_geographic_area,
	ensure_high_priority_assignment,
	ensure_impact_taxonomy,
)


class TestNotifications(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.lead_user = cls._ensure_user("srm-lead-notify@test.com", "SRM Lead")
		cls.analyst_user = cls._ensure_user("srm-analyst-notify@test.com", "SRM Analyst")

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
		area = ensure_geographic_area(f"Notify Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Notification Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Notification test incident",
			"incident_owner": "Administrator",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _make_event(self, incident_name, event_type, summary, details):
		return emit_incident_event(
			incident=incident_name,
			event_type=event_type,
			summary=summary,
			details=details,
		)

	def test_escalation_rule_notifies_owner_and_open_task_assignees(self):
		doc = self._make_incident()
		doc.append(
			"investigation_tasks",
			{
				"task_title": "Review escalation",
				"assignee": self.analyst_user,
				"status": TASK_STATUS_OPEN,
			},
		)
		doc.insert()
		event = self._make_event(
			doc.name,
			EVENT_ESCALATION_CHANGED,
			"Escalation changed: None -> L2",
			{"previous_level": "None", "current_level": "L2", "is_escalated": 1},
		)
		intents = evaluate_incident_event_for_notifications(event)
		recipients = {intent["recipient"] for intent in intents}
		self.assertIn("Administrator", recipients)
		self.assertIn(self.analyst_user, recipients)
		channels = {(intent["recipient"], intent["channel"]) for intent in intents}
		self.assertIn(("Administrator", CHANNEL_IN_APP), channels)
		self.assertIn(("Administrator", CHANNEL_EMAIL), channels)

	def test_sla_due_within_six_hours_rule(self):
		doc = self._make_incident()
		doc.insert()
		due = add_to_date(now_datetime(), hours=4)
		event = self._make_event(
			doc.name,
			EVENT_SLA_UPDATED,
			f"SLA updated due {due}",
			{"sla_target_hours": 4, "sla_due_by": str(due)},
		)
		intents = evaluate_incident_event_for_notifications(event)
		self.assertTrue(any(intent["rule_key"] == RULE_SLA_DUE_6H for intent in intents))
		self.assertEqual(len({intent["recipient"] for intent in intents}), 1)

	def test_status_closed_notifies_owner_and_task_assignees(self):
		doc = self._make_incident()
		doc.append(
			"investigation_tasks",
			{
				"task_title": "Closeout task",
				"assignee": self.analyst_user,
				"status": "Done",
			},
		)
		doc.insert()
		event = self._make_event(
			doc.name,
			EVENT_STATUS_CHANGED,
			"Status changed: Open -> Closed",
			{"previous_status": "Open", "current_status": "Closed"},
		)
		intents = evaluate_incident_event_for_notifications(event)
		recipients = {intent["recipient"] for intent in intents}
		self.assertIn("Administrator", recipients)
		self.assertIn(self.analyst_user, recipients)

	def test_priority_p1_notifies_owner_and_srm_lead(self):
		doc = self._make_incident(incident_owner=self.lead_user)
		doc.insert()
		event = self._make_event(
			doc.name,
			EVENT_PRIORITY_COMPUTED,
			"Priority computed: P1-Critical (100.0)",
			{"priority_score": 100.0, "priority_level": "P1-Critical"},
		)
		intents = evaluate_incident_event_for_notifications(event)
		recipients = {intent["recipient"] for intent in intents}
		self.assertIn(self.lead_user, recipients)
		self.assertTrue(any(intent["rule_key"] == RULE_PRIORITY_P1 for intent in intents))

	def test_recipient_dedupe_per_event_rule_and_channel(self):
		doc = self._make_incident()
		doc.insert()
		event = self._make_event(
			doc.name,
			EVENT_ESCALATION_CHANGED,
			"Escalation changed: None -> L3",
			{"previous_level": "None", "current_level": "L3", "is_escalated": 1},
		)
		intents = evaluate_incident_event_for_notifications(event)
		keys = {(i["recipient"], i["channel"], i["rule_key"]) for i in intents}
		self.assertEqual(len(keys), len(intents))

	def test_idempotency_prevents_duplicate_notifications(self):
		doc = self._make_incident()
		doc.insert()
		event_doc = frappe.get_doc(
			{
				"doctype": "SRM Incident Event",
				"incident": doc.name,
				"event_type": EVENT_ESCALATION_CHANGED,
				"event_time": now_datetime(),
				"summary": "Escalation changed: None -> L2",
				"details_json": json.dumps(
					{"previous_level": "None", "current_level": "L2", "is_escalated": 1}
				),
			}
		)
		event_doc.insert(ignore_permissions=True)
		intents = evaluate_incident_event_for_notifications(event_doc)
		first = queue_notifications(intents)
		second = queue_notifications(intents)
		self.assertGreater(len(first), 0)
		self.assertEqual(len(second), 0)

	def test_dispatch_marks_in_app_sent_and_email_failed_without_email(self):
		doc = self._make_incident()
		doc.insert()
		no_email_user = self._ensure_user("no-email-notify@test.com", "SRM Analyst")
		frappe.db.set_value("User", no_email_user, "email", "")
		intents = [
			{
				"incident": doc.name,
				"event": None,
				"recipient": "Administrator",
				"channel": CHANNEL_IN_APP,
				"subject": "In-app test",
				"message": "In-app body",
				"rule_key": RULE_ESCALATION_L2_L3,
			},
			{
				"incident": doc.name,
				"event": None,
				"recipient": no_email_user,
				"channel": CHANNEL_EMAIL,
				"subject": "Email test",
				"message": "Email body",
				"rule_key": RULE_ESCALATION_L2_L3,
			},
		]
		queued = queue_notifications(intents)
		self.assertEqual(len(queued), 2)
		results = dispatch_queued_notifications()
		self.assertGreaterEqual(results["sent"], 1)
		self.assertGreaterEqual(results["failed"], 1)
		self.assertEqual(
			frappe.db.get_value("SRM Notification", queued[0], "status"),
			STATUS_SENT,
		)

	def test_mark_read_permission_checks(self):
		doc = self._make_incident()
		doc.insert()
		event = self._make_event(
			doc.name,
			EVENT_ESCALATION_CHANGED,
			"Escalation changed: None -> L2",
			{"previous_level": "None", "current_level": "L2", "is_escalated": 1},
		)
		in_app = frappe.db.get_value(
			"SRM Notification",
			{
				"event": event.name,
				"channel": CHANNEL_IN_APP,
				"recipient": "Administrator",
			},
			"name",
		)
		self.assertTrue(in_app)

		frappe.set_user(self.analyst_user)
		with self.assertRaises(frappe.ValidationError):
			mark_notification_read(in_app, user=self.analyst_user)

		frappe.set_user("Administrator")
		mark_notification_read(in_app, user="Administrator")
		self.assertEqual(frappe.db.get_value("SRM Notification", in_app, "is_read"), 1)

	def test_integration_incident_change_queues_notifications(self):
		taxonomy = ensure_impact_taxonomy(f"Notify Escalation Taxonomy {random_string(6)}")
		doc = self._make_incident(
			incident_owner=self.lead_user,
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Very High"},
			],
		)
		ensure_high_priority_assignment(doc, assignee=self.analyst_user)
		before = frappe.db.count("SRM Notification", {"incident": doc.name})
		doc.insert()
		after = frappe.db.count("SRM Notification", {"incident": doc.name})
		self.assertGreater(after, before)
		self.assertTrue(
			frappe.db.exists(
				"SRM Notification",
				{
					"incident": doc.name,
					"rule_key": RULE_ESCALATION_L2_L3,
					"status": STATUS_SENT,
				},
			)
		)
		unread = get_unread_in_app_notifications(self.lead_user)
		self.assertTrue(any(row["incident"] == doc.name for row in unread))

	def test_process_same_event_twice_does_not_duplicate(self):
		doc = self._make_incident()
		doc.insert()
		event = self._make_event(
			doc.name,
			EVENT_ESCALATION_CHANGED,
			"Escalation changed: None -> L2",
			{"previous_level": "None", "current_level": "L2", "is_escalated": 1},
		)
		before = frappe.db.count("SRM Notification", {"event": event.name})
		process_notifications_for_event(event)
		after = frappe.db.count("SRM Notification", {"event": event.name})
		self.assertEqual(before, after)
