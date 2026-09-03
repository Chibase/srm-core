"""Incident comment helpers and mention parsing for SRM Core."""

import re

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

MAX_COMMENT_LENGTH = 5000
MENTION_PATTERN = re.compile(r"@([\w@.-]+)")

SOURCE_USER = "user"
SOURCE_SYSTEM = "system"


def resolve_mention_user(token):
	"""Resolve @mention token to a User name; return None when unresolved."""
	if not token:
		return None
	if frappe.db.exists("User", token):
		return token
	matches = frappe.get_all(
		"User",
		filters={"email": token},
		pluck="name",
		limit=1,
	)
	return matches[0] if matches else None


def parse_mentions_from_text(text):
	"""Parse @username mentions from plain text; dedupe while preserving order."""
	users = []
	seen = set()
	for token in MENTION_PATTERN.findall(text or ""):
		user = resolve_mention_user(token)
		if not user or user in seen:
			continue
		seen.add(user)
		users.append(user)
	return users


def serialize_mention_users(users):
	"""Persist mentions as comma-separated usernames."""
	return ",".join(users or [])


def parse_mention_users_field(value):
	"""Parse stored mention_users CSV into a list."""
	if not value:
		return []
	return [user.strip() for user in str(value).split(",") if user.strip()]


def validate_incident_comment_rows(rows, previous_rows=None):
	"""Validate and stamp incident comment child rows."""
	if not rows:
		return

	previous_by_name = {row.name: row for row in (previous_rows or []) if row.name}
	now = now_datetime()
	user = frappe.session.user

	for row in rows:
		text = (row.comment_text or "").strip()
		if not text:
			frappe.throw(_("Comment text cannot be empty."))

		if len(row.comment_text or "") > MAX_COMMENT_LENGTH:
			frappe.throw(
				_("Comment text exceeds the maximum length of {0} characters.").format(MAX_COMMENT_LENGTH)
			)

		is_new_row = (
			getattr(row, "is_new", lambda: True)() or not row.name or row.name not in previous_by_name
		)
		if is_new_row:
			row.comment_by = row.comment_by or user
			row.comment_on = row.comment_on or now
			row.source = row.source or SOURCE_USER
		else:
			previous = previous_by_name.get(row.name)
			if previous and previous.comment_text != row.comment_text:
				row.edited_on = now
				row.edited_by = user

		row.mention_users = serialize_mention_users(parse_mentions_from_text(row.comment_text))


def diff_incident_comments(previous_rows, current_rows):
	"""Return newly added comment rows."""
	previous_rows = previous_rows or []
	current_rows = current_rows or []

	previous_keys = set()
	for row in previous_rows:
		previous_keys.add(row.name or f"{row.idx}|{row.comment_on}|{row.comment_text}")

	added = []
	for row in current_rows:
		key = row.name or f"{row.idx}|{row.comment_on}|{row.comment_text}"
		if key not in previous_keys:
			added.append(row)
	return added


def get_incident_comments(incident_name, limit=200, include_internal=True):
	"""Return incident comments ordered ascending by comment_on.

	Callers must enforce authorization before invoking this helper, for example::

	    frappe.has_permission("SRM Incident", "read", incident_name, throw=True)
	    comments = get_incident_comments(incident_name)
	"""
	filters = {
		"parent": incident_name,
		"parenttype": "SRM Incident",
		"parentfield": "comments",
	}
	if not include_internal:
		filters["is_internal"] = 0

	return frappe.get_all(
		"SRM Incident Comment",
		filters=filters,
		fields=[
			"name",
			"comment_by",
			"comment_on",
			"comment_text",
			"is_internal",
			"edited_on",
			"edited_by",
			"mention_users",
			"source",
		],
		order_by="comment_on asc, idx asc",
		limit=limit,
	)
