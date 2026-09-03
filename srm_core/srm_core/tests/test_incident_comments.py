# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, random_string

from srm_core.services.comments import (
	MAX_COMMENT_LENGTH,
	get_incident_comments,
	parse_mention_users_field,
	parse_mentions_from_text,
	serialize_mention_users,
)
from srm_core.services.notifications import RULE_COMMENT_MENTION, STATUS_SENT
from srm_core.services.permissions import ensure_srm_roles
from srm_core.services.timeline import EVENT_COMMENT_ADDED
from srm_core.srm_core.tests.test_helpers import ensure_geographic_area


class TestIncidentComments(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_srm_roles()
		cls.analyst_user = cls._ensure_user("srm-analyst-comments@test.com", "SRM Analyst")

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
		area = ensure_geographic_area(f"Comment Ward {random_string(6)}")
		data = {
			"doctype": "SRM Incident",
			"incident_title": "Comment Test Incident",
			"incident_date": "2026-07-02",
			"incident_channel": "Phone",
			"geographic_area": area,
			"geographic_area_text": area,
			"severity": "Medium",
			"status": "Open",
			"description": "Comment test incident",
		}
		data.update(overrides)
		return frappe.get_doc(data)

	def test_add_comment_stamps_by_and_on(self):
		doc = self._make_incident()
		doc.append(
			"comments",
			{"comment_text": "Initial investigation note.", "is_internal": 1},
		)
		before = now_datetime()
		doc.insert()
		comment = doc.comments[0]
		self.assertEqual(comment.comment_by, "Administrator")
		self.assertTrue(comment.comment_on)
		self.assertGreaterEqual(
			frappe.utils.get_datetime(comment.comment_on),
			frappe.utils.add_to_date(before, seconds=-5),
		)

	def test_edit_comment_stamps_edited_fields(self):
		doc = self._make_incident()
		doc.append("comments", {"comment_text": "Original comment text."})
		doc.insert()
		doc.comments[0].comment_text = "Updated comment text."
		doc.save()
		comment = doc.comments[0]
		self.assertTrue(comment.edited_on)
		self.assertEqual(comment.edited_by, "Administrator")

	def test_mention_parsing_single_multiple_duplicates_punctuation(self):
		users = parse_mentions_from_text(
			f"Please review @{self.analyst_user}, cc @{self.analyst_user} and @missing-user-xyz."
		)
		self.assertEqual(users, [self.analyst_user])
		self.assertEqual(
			parse_mentions_from_text(f"Thanks @{self.analyst_user}!"),
			[self.analyst_user],
		)
		self.assertEqual(
			serialize_mention_users([self.analyst_user, "Administrator"]),
			f"{self.analyst_user},Administrator",
		)
		self.assertEqual(
			parse_mention_users_field(serialize_mention_users([self.analyst_user])),
			[self.analyst_user],
		)

	def test_empty_comment_rejection(self):
		doc = self._make_incident()
		doc.append("comments", {"comment_text": "   "})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_comment_max_length_guard(self):
		doc = self._make_incident()
		doc.append("comments", {"comment_text": "x" * (MAX_COMMENT_LENGTH + 1)})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_comment_added_timeline_event_emitted_once(self):
		doc = self._make_incident()
		doc.insert()
		before = frappe.db.count(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_COMMENT_ADDED},
		)
		doc.append("comments", {"comment_text": "Timeline comment event test."})
		doc.save()
		after = frappe.db.count(
			"SRM Incident Event",
			{"incident": doc.name, "event_type": EVENT_COMMENT_ADDED},
		)
		self.assertEqual(after, before + 1)

		doc.save()
		self.assertEqual(
			frappe.db.count(
				"SRM Incident Event",
				{"incident": doc.name, "event_type": EVENT_COMMENT_ADDED},
			),
			after,
		)

	def test_mention_notification_creation_dedupe_and_no_self_notify(self):
		doc = self._make_incident()
		doc.append(
			"comments",
			{
				"comment_text": (f"Looping in @{self.analyst_user} and @Administrator for review."),
			},
		)
		doc.insert()
		self.assertTrue(
			frappe.db.exists(
				"SRM Notification",
				{
					"incident": doc.name,
					"recipient": self.analyst_user,
					"rule_key": RULE_COMMENT_MENTION,
					"status": STATUS_SENT,
				},
			)
		)
		self.assertFalse(
			frappe.db.exists(
				"SRM Notification",
				{
					"incident": doc.name,
					"recipient": "Administrator",
					"rule_key": RULE_COMMENT_MENTION,
				},
			)
		)
		count = frappe.db.count(
			"SRM Notification",
			{
				"incident": doc.name,
				"recipient": self.analyst_user,
				"rule_key": RULE_COMMENT_MENTION,
			},
		)
		self.assertEqual(count, 2)

	def test_unresolved_mentions_ignored(self):
		mentions = parse_mentions_from_text("@definitely-not-a-real-user-xyz")
		self.assertEqual(mentions, [])

	def test_get_incident_comments_filters_internal(self):
		doc = self._make_incident()
		doc.append("comments", {"comment_text": "Internal note", "is_internal": 1})
		doc.append("comments", {"comment_text": "External note", "is_internal": 0})
		doc.insert()
		all_comments = get_incident_comments(doc.name)
		public_comments = get_incident_comments(doc.name, include_internal=False)
		self.assertEqual(len(all_comments), 2)
		self.assertEqual(len(public_comments), 1)
		self.assertEqual(public_comments[0]["comment_text"], "External note")

	def test_comment_event_payload_includes_mention_count(self):
		doc = self._make_incident()
		doc.append(
			"comments",
			{"comment_text": f"Ping @{self.analyst_user} about this incident."},
		)
		doc.insert()
		event = frappe.get_all(
			"SRM Incident Event",
			filters={"incident": doc.name, "event_type": EVENT_COMMENT_ADDED},
			fields=["details_json"],
			limit=1,
		)[0]
		payload = json.loads(event.details_json)
		self.assertEqual(payload["mention_count"], 1)
		self.assertIn(self.analyst_user, payload["mentioned_users"])
