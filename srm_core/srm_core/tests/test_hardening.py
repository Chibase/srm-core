# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, random_string

from srm_core.ops.maintenance import (
	rebuild_incident_timeline,
	recompute_priority_and_sla,
	recompute_residual_risk,
	requeue_failed_notifications,
)
from srm_core.patches.v1_0.verify_and_repair_hardening_invariants import execute as repair_hardening
from srm_core.services.idempotency import is_duplicate_entry_error
from srm_core.services.notifications import (
	STATUS_FAILED,
	STATUS_SENT,
	make_notification_idempotency_key,
	process_notifications_for_event,
)
from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.timeline import (
	EVENT_INCIDENT_CREATED,
	emit_incident_event,
	make_idempotency_key,
)
from srm_core.srm_core.tests.test_helpers import (
	ensure_geographic_area,
	ensure_high_priority_assignment,
	ensure_impact_taxonomy,
	ensure_risk_register,
)


class TestProductionHardening(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.lead_user = cls._ensure_user("srm-lead-hardening@test.com", "SRM Lead")

	@classmethod
	def _ensure_user(cls, email, role):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"roles": [{"role": role}],
				}
			).insert(ignore_permissions=True)
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
		area = ensure_geographic_area(f"Hardening Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Hardening Smoke Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Production hardening smoke incident",
			"incident_owner": self.lead_user,
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def test_duplicate_event_emit_is_idempotent(self):
		doc = self._make_incident()
		doc.insert()
		before = frappe.db.count("SRM Incident Event", {"incident": doc.name})
		snapshot = {"incident": doc.name, "status": doc.status}
		key = make_idempotency_key(doc.name, EVENT_INCIDENT_CREATED, snapshot)
		self.assertIsNone(
			emit_incident_event(
				incident=doc.name,
				event_type=EVENT_INCIDENT_CREATED,
				summary="Duplicate emit",
				details=snapshot,
				idempotency_key=key,
			)
		)
		self.assertIsNone(
			emit_incident_event(
				incident=doc.name,
				event_type=EVENT_INCIDENT_CREATED,
				summary="Duplicate emit again",
				details=snapshot,
				idempotency_key=key,
			)
		)
		self.assertEqual(frappe.db.count("SRM Incident Event", {"incident": doc.name}), before)

	def test_duplicate_notification_queue_is_idempotent(self):
		doc = self._make_incident()
		doc.insert()
		event = frappe.get_all(
			"SRM Incident Event",
			filters={"incident": doc.name},
			fields=["name"],
			limit=1,
		)[0]
		event_doc = frappe.get_doc("SRM Incident Event", event.name)
		first = process_notifications_for_event(event_doc)
		second = process_notifications_for_event(event_doc)
		self.assertGreaterEqual(len(first["queued"]), 0)
		self.assertEqual(second["queued"], [])

	def test_is_duplicate_entry_error_detects_integrity_conflicts(self):
		self.assertTrue(is_duplicate_entry_error(frappe.DuplicateEntryError("duplicate")))

	def test_rebuild_incident_timeline_is_idempotent(self):
		doc = self._make_incident()
		doc.insert()
		first = rebuild_incident_timeline(incident=doc.name)
		second = rebuild_incident_timeline(incident=doc.name)
		self.assertEqual(first["operation"], "rebuild_incident_timeline")
		self.assertEqual(first["processed"], 1)
		self.assertEqual(second["created_events"], 0)
		self.assertEqual(second["status_snapshot_events"], 0)

	def test_recompute_residual_risk_summary_is_stable(self):
		taxonomy = ensure_impact_taxonomy(f"Hardening Taxonomy {random_string(6)}")
		risk = ensure_risk_register(f"Hardening Risk {random_string(6)}")
		doc = self._make_incident(
			linked_risk=risk,
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "High"},
			],
		)
		ensure_high_priority_assignment(doc)
		doc.insert()
		first = recompute_residual_risk(incident=doc.name)
		second = recompute_residual_risk(incident=doc.name)
		self.assertEqual(first["processed"], 1)
		self.assertEqual(second["updated"], 0)

	def test_recompute_priority_and_sla_returns_summary(self):
		doc = self._make_incident()
		doc.insert()
		summary = recompute_priority_and_sla(incident=doc.name)
		self.assertEqual(summary["operation"], "recompute_priority_and_sla")
		self.assertEqual(summary["processed"], 1)
		self.assertEqual(summary["updated"], 1)

	def test_requeue_failed_notifications_summary(self):
		doc = self._make_incident()
		doc.insert()
		key = make_notification_idempotency_key(
			doc.name,
			None,
			self.lead_user,
			"in_app",
			"hardening_failed_test",
		)
		notification = frappe.get_doc(
			{
				"doctype": "SRM Notification",
				"incident": doc.name,
				"recipient": self.lead_user,
				"channel": "in_app",
				"subject": "Failed test",
				"message": "Failed test",
				"status": STATUS_FAILED,
				"rule_key": "hardening_failed_test",
				"idempotency_key": key,
				"queued_on": now_datetime(),
			}
		)
		notification.insert(ignore_permissions=True)
		summary = requeue_failed_notifications(limit=10)
		self.assertGreaterEqual(summary["requeued"], 1)
		self.assertEqual(
			frappe.db.get_value("SRM Notification", notification.name, "status"),
			STATUS_SENT,
		)

	def test_repair_patch_is_idempotent(self):
		repair_hardening()
		repair_hardening()

	def test_lifecycle_smoke_end_to_end(self):
		taxonomy = ensure_impact_taxonomy(f"Smoke Taxonomy {random_string(6)}")
		risk = ensure_risk_register(f"Smoke Risk {random_string(6)}")
		doc = self._make_incident(
			linked_risk=risk,
			impact_assessments=[
				{"impact_taxonomy": taxonomy, "observed_severity": "Medium"},
			],
		)
		ensure_high_priority_assignment(doc)
		doc.append(
			"comments",
			{"comment_text": "Smoke comment for hardening path."},
		)
		doc.append(
			"attachments",
			{
				"file_url": "/files/smoke/evidence.pdf",
				"file_name": "evidence.pdf",
				"evidence_type": "document",
				"classification": "internal",
			},
		)
		doc.insert()
		self.assertTrue(doc.impact_score)
		self.assertTrue(doc.priority_level)
		self.assertTrue(doc.residual_risk_band)
		self.assertTrue(
			frappe.db.count("SRM Incident Event", {"incident": doc.name}) >= 5
		)
		self.assertTrue(
			frappe.db.count("SRM Notification", {"incident": doc.name}) >= 1
		)

	def test_non_system_manager_cannot_run_maintenance(self):
		frappe.set_user(self.lead_user)
		with self.assertRaises(frappe.ValidationError):
			rebuild_incident_timeline(limit=1)
