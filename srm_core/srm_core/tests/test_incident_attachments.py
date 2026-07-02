# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, random_string

from srm_core.services.attachments import (
	compute_integrity_hash,
	get_incident_attachments,
	normalize_file_name,
)
from srm_core.services.notifications import RULE_SENSITIVE_EVIDENCE_ADDED, STATUS_SENT
from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.timeline import EVENT_ATTACHMENT_ADDED, EVENT_ATTACHMENT_REMOVED
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area


class TestIncidentAttachments(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.lead_user = cls._ensure_user("srm-lead-attach@test.com", "SRM Lead")
		cls.case_manager_user = cls._ensure_user(
			"srm-case-manager-attach@test.com", "SRM Case Manager"
		)

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
		area = ensure_geographic_area(f"Attachment Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Attachment Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Attachment test incident",
			"incident_owner": self.lead_user,
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _attachment_row(self, **overrides):
		data = {
			"file_url": "/files/evidence/test.pdf",
			"file_name": "test.pdf",
			"evidence_type": "document",
			"classification": "internal",
		}
		data.update(overrides)
		return data

	def test_add_valid_attachment_row(self):
		doc = self._make_incident()
		doc.append("attachments", self._attachment_row())
		before = now_datetime()
		doc.insert()
		attachment = doc.attachments[0]
		self.assertEqual(attachment.attached_by, "Administrator")
		self.assertTrue(attachment.attached_on)
		self.assertGreaterEqual(
			frappe.utils.get_datetime(attachment.attached_on),
			frappe.utils.add_to_date(before, seconds=-5),
		)

	def test_required_field_validation(self):
		doc = self._make_incident()
		doc.append(
			"attachments",
			{
				"file_url": "/files/evidence/missing-meta.pdf",
				"file_name": "missing-meta.pdf",
				"evidence_type": "",
				"classification": "",
			},
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_single_active_primary_evidence_enforcement(self):
		doc = self._make_incident()
		doc.append(
			"attachments",
			self._attachment_row(
				file_url="/files/evidence/primary-a.pdf",
				file_name="primary-a.pdf",
				is_primary_evidence=1,
			),
		)
		doc.append(
			"attachments",
			self._attachment_row(
				file_url="/files/evidence/primary-b.pdf",
				file_name="primary-b.pdf",
				is_primary_evidence=1,
			),
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_soft_remove_stamps_and_requires_reason(self):
		doc = self._make_incident()
		doc.append("attachments", self._attachment_row())
		doc.insert()
		doc.attachments[0].is_removed = 1
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		doc.reload()

		doc.attachments[0].is_removed = 1
		doc.attachments[0].removal_reason = "Duplicate upload."
		doc.save()
		attachment = doc.attachments[0]
		self.assertEqual(attachment.removed_by, "Administrator")
		self.assertTrue(attachment.removed_on)

	def test_restore_removed_attachment_only_by_system_manager(self):
		doc = self._make_incident()
		doc.append("attachments", self._attachment_row())
		doc.insert()
		doc.attachments[0].is_removed = 1
		doc.attachments[0].removal_reason = "Uploaded in error."
		doc.save()

		frappe.set_user(self.case_manager_user)
		doc.reload()
		doc.attachments[0].is_removed = 0
		with self.assertRaises(frappe.ValidationError):
			doc.save()

		frappe.set_user("Administrator")
		doc.reload()
		doc.attachments[0].is_removed = 0
		doc.save()
		attachment = doc.attachments[0]
		self.assertEqual(attachment.is_removed, 0)
		self.assertFalse(attachment.removed_on)
		self.assertFalse(attachment.removal_reason)

	def test_closed_incident_add_remove_blocked_for_non_system_manager(self):
		doc = self._make_incident(status="Open")
		doc.insert()
		doc.submit()
		doc.status = "Resolved"
		doc.resolution_summary = "Resolved for closure."
		doc.save()
		doc.status = "Closed"
		doc.resolution_summary = "Closed for attachment guard test."
		doc.save()

		frappe.set_user(self.case_manager_user)
		doc.append(
			"attachments",
			self._attachment_row(file_url="/files/evidence/closed-add.pdf", file_name="closed-add.pdf"),
		)
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_closed_incident_system_manager_override(self):
		doc = self._make_incident(status="Open")
		doc.append("attachments", self._attachment_row(file_name="existing.pdf"))
		doc.insert()
		doc.submit()
		doc.status = "Resolved"
		doc.resolution_summary = "Resolved."
		doc.save()
		doc.status = "Closed"
		doc.resolution_summary = "Closed."
		doc.save()

		frappe.set_user("Administrator")
		doc.append(
			"attachments",
			self._attachment_row(
				file_url="/files/evidence/closed-override.pdf",
				file_name="closed-override.pdf",
			),
		)
		doc.save()
		self.assertEqual(len(doc.attachments), 2)

	def test_attachment_timeline_events_emitted_once(self):
		doc = self._make_incident()
		doc.insert()
		before_added = frappe.db.count(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_ATTACHMENT_ADDED},
		)
		doc.append("attachments", self._attachment_row(file_name="timeline.pdf"))
		doc.save()
		after_added = frappe.db.count(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_ATTACHMENT_ADDED},
		)
		self.assertEqual(after_added, before_added + 1)

		doc.attachments[0].is_removed = 1
		doc.attachments[0].removal_reason = "No longer relevant."
		doc.save()
		self.assertEqual(
			frappe.db.count(
				"SRM Incident Event",
				{"incident": doc.name, "event_type": EVENT_ATTACHMENT_REMOVED},
			),
			1,
		)

		doc.save()
		self.assertEqual(
			frappe.db.count(
				"SRM Incident Event",
				{"incident": doc.name, "event_type": EVENT_ATTACHMENT_ADDED},
			),
			after_added,
		)

	def test_sensitive_evidence_notification_triggered(self):
		doc = self._make_incident(incident_owner=self.lead_user)
		doc.append(
			"attachments",
			self._attachment_row(
				file_url="/files/evidence/restricted.pdf",
				file_name="restricted.pdf",
				classification="restricted",
			),
		)
		doc.insert()
		self.assertTrue(
			frappe.db.exists(
				"SRM Notification",
				{
					"incident": doc.name,
					"recipient": self.lead_user,
					"rule_key": RULE_SENSITIVE_EVIDENCE_ADDED,
					"status": STATUS_SENT,
				},
			)
		)

	def test_integrity_hash_and_read_helper(self):
		content = b"sample evidence bytes"
		expected = compute_integrity_hash(content)
		self.assertEqual(len(expected), 64)
		self.assertEqual(compute_integrity_hash(content), expected)
		self.assertEqual(normalize_file_name("/files/evidence/nested/file.log"), "file.log")

		doc = self._make_incident()
		doc.append(
			"attachments",
			self._attachment_row(
				file_name="public.txt",
				classification="public",
				integrity_hash=compute_integrity_hash(content),
			),
		)
		doc.append(
			"attachments",
			self._attachment_row(
				file_url="/files/evidence/removed.txt",
				file_name="removed.txt",
				classification="internal",
			),
		)
		doc.insert()
		doc.reload()
		doc.attachments[1].is_removed = 1
		doc.attachments[1].removal_reason = "Test removal."
		doc.save()

		active = get_incident_attachments(doc.name)
		self.assertEqual(len(active), 1)
		public_only = get_incident_attachments(doc.name, classification="public")
		self.assertEqual(len(public_only), 1)
		with_removed = get_incident_attachments(doc.name, include_removed=True)
		self.assertEqual(len(with_removed), 2)

	def test_attachment_event_payload(self):
		doc = self._make_incident()
		doc.append(
			"attachments",
			self._attachment_row(
				file_name="payload.pdf",
				classification="confidential",
				is_primary_evidence=1,
			),
		)
		doc.insert()
		event = frappe.get_all(
			"SRM Incident Event",
			filters={"incident": doc.name, "event_type": EVENT_ATTACHMENT_ADDED},
			fields=["details_json"],
			limit=1,
		)[0]
		payload = json.loads(event.details_json)
		self.assertEqual(payload["file_name"], "payload.pdf")
		self.assertEqual(payload["classification"], "confidential")
		self.assertEqual(payload["is_primary_evidence"], 1)
