# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime, random_string

from srm_core.services.investigation_tasks import (
	TASK_STATUS_BLOCKED,
	TASK_STATUS_DONE,
	TASK_STATUS_IN_PROGRESS,
	TASK_STATUS_OPEN,
	apply_status_transition,
	format_blocking_tasks_message,
	get_blocking_tasks,
)
from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.statuses import INCIDENT_CLOSED, INCIDENT_OPEN
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area


class TestInvestigationTasks(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.analyst_user = cls._ensure_user("srm-analyst-tasks@test.com", "SRM Analyst")
		cls.case_manager_user = cls._ensure_user(
			"srm-case-manager-tasks@test.com", "SRM Case Manager"
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
		area = ensure_geographic_area(f"Task Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Investigation Task Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": INCIDENT_OPEN,
			"description": "Investigation task test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def _task_row(self, **overrides):
		data = {
			"task_title": "Interview witnesses",
			"assignee": self.analyst_user,
			"status": TASK_STATUS_OPEN,
			"priority": "Medium",
		}
		data.update(overrides)
		return data

	def test_add_valid_task_rows(self):
		doc = self._make_incident()
		doc.append("investigation_tasks", self._task_row(task_description="Gather statements."))
		doc.insert()
		self.assertEqual(len(doc.investigation_tasks), 1)
		self.assertEqual(doc.investigation_tasks[0].task_title, "Interview witnesses")
		self.assertEqual(doc.investigation_tasks[0].assignee, self.analyst_user)

	def test_duplicate_open_task_rejection(self):
		doc = self._make_incident()
		doc.append("investigation_tasks", self._task_row())
		doc.append("investigation_tasks", self._task_row(status=TASK_STATUS_IN_PROGRESS))
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_done_auto_stamps_completed_on(self):
		doc = self._make_incident()
		doc.append("investigation_tasks", self._task_row(status=TASK_STATUS_DONE))
		before = now_datetime()
		doc.insert()
		self.assertTrue(doc.investigation_tasks[0].completed_on)
		self.assertGreaterEqual(
			frappe.utils.get_datetime(doc.investigation_tasks[0].completed_on),
			add_to_date(before, seconds=-5),
		)

	def test_reopening_task_clears_completed_on(self):
		doc = self._make_incident()
		doc.append("investigation_tasks", self._task_row(status=TASK_STATUS_DONE))
		doc.insert()
		self.assertTrue(doc.investigation_tasks[0].completed_on)

		doc.investigation_tasks[0].status = TASK_STATUS_OPEN
		doc.save()
		self.assertIsNone(doc.investigation_tasks[0].completed_on)

	def test_cannot_close_incident_with_blocking_tasks_non_system_manager(self):
		doc = self._make_incident()
		doc.append("investigation_tasks", self._task_row(status=TASK_STATUS_BLOCKED))
		doc.insert()
		doc.submit()

		frappe.set_user(self.case_manager_user)
		doc.status = INCIDENT_CLOSED
		doc.resolution_summary = "Attempted close with open tasks."
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_system_manager_override_can_close_with_blocking_tasks(self):
		doc = self._make_incident()
		doc.append("investigation_tasks", self._task_row(status=TASK_STATUS_IN_PROGRESS))
		doc.insert()
		doc.submit()

		frappe.set_user("Administrator")
		doc.status = INCIDENT_CLOSED
		doc.resolution_summary = "Closed by System Manager override."
		doc.save()
		doc.reload()
		self.assertEqual(doc.status, INCIDENT_CLOSED)

	def test_blocking_list_message_formatting(self):
		blocking = [
			frappe._dict({"task_title": f"Task {index}", "status": TASK_STATUS_OPEN})
			for index in range(1, 8)
		]
		message = format_blocking_tasks_message(blocking)
		self.assertIn("Task 1", message)
		self.assertIn("Task 5", message)
		self.assertNotIn("Task 6", message)
		self.assertIn("...and 2 more", message)

	def test_status_transition_helper_is_deterministic(self):
		row = frappe._dict({"status": TASK_STATUS_OPEN, "completed_on": None})
		fixed_now = now_datetime()
		apply_status_transition(row, now=fixed_now)
		self.assertIsNone(row.completed_on)

		row.status = TASK_STATUS_DONE
		apply_status_transition(row, now=fixed_now)
		self.assertEqual(row.completed_on, fixed_now)

		row.status = TASK_STATUS_OPEN
		apply_status_transition(row, now=fixed_now)
		self.assertIsNone(row.completed_on)

	def test_get_blocking_tasks_excludes_done_and_cancelled(self):
		rows = [
			frappe._dict({"task_title": "Open task", "status": TASK_STATUS_OPEN}),
			frappe._dict({"task_title": "Done task", "status": TASK_STATUS_DONE}),
			frappe._dict({"task_title": "Cancelled task", "status": "Cancelled"}),
		]
		blocking = get_blocking_tasks(rows)
		self.assertEqual(len(blocking), 1)
		self.assertEqual(blocking[0].task_title, "Open task")
