# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.statuses import INCIDENT_CLOSED, INCIDENT_OPEN


class TestIKSPermissions(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.users = {
			"admin": cls._ensure_user("srm-admin@test.com", "SRM Admin"),
			"case_manager": cls._ensure_user("srm-case-manager@test.com", "SRM Case Manager"),
		}

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

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

	def _make_iks_incident(self, **overrides):
		data = {
			"doctype": "SRM Incident",
			"incident_title": "IKS Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area_text": "Ward 12",
			"severity": "Medium",
			"status": INCIDENT_OPEN,
			"description": "IKS test description",
			"iks_sensitive": 1,
			"consent_obtained": 1,
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _submit_iks_incident(self):
		frappe.set_user("Administrator")
		doc = self._make_iks_incident()
		doc.insert()
		doc.submit()
		return doc

	def test_non_admin_cannot_close_iks_sensitive_incident(self):
		doc = self._submit_iks_incident()
		frappe.set_user(self.users["case_manager"])
		doc.status = INCIDENT_CLOSED
		doc.resolution_summary = "Attempted close by case manager."
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_admin_can_close_iks_sensitive_incident(self):
		doc = self._submit_iks_incident()
		frappe.set_user(self.users["admin"])
		doc.status = INCIDENT_CLOSED
		doc.resolution_summary = "Closed by SRM Admin."
		doc.save()
		doc.reload()
		self.assertEqual(doc.status, INCIDENT_CLOSED)
		self.assertEqual(doc.last_sensitive_action_by, self.users["admin"])

	def test_non_admin_cannot_update_resolution_summary_post_submit(self):
		doc = self._submit_iks_incident()
		frappe.set_user(self.users["case_manager"])
		doc.resolution_summary = "Unauthorized summary update."
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_admin_resolution_summary_update_sets_audit_fields(self):
		doc = self._submit_iks_incident()
		frappe.set_user(self.users["admin"])
		doc.resolution_summary = "Authorized summary update."
		doc.save()
		doc.reload()
		self.assertEqual(doc.resolution_summary, "Authorized summary update.")
		self.assertEqual(doc.last_sensitive_action_by, self.users["admin"])
		self.assertTrue(doc.last_sensitive_action_on)

	def test_iks_sensitive_still_requires_consent(self):
		frappe.set_user("Administrator")
		doc = self._make_iks_incident(consent_obtained=0)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_srm_viewer_cannot_create_incident(self):
		viewer = self._ensure_user("srm-viewer@test.com", "SRM Viewer")
		frappe.set_user(viewer)
		doc = self._make_iks_incident(iks_sensitive=0, consent_obtained=0)
		with self.assertRaises(frappe.PermissionError):
			doc.insert()
