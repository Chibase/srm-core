"""Investigation task helpers for SRM Core."""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

TASK_STATUS_OPEN = "Open"
TASK_STATUS_IN_PROGRESS = "In Progress"
TASK_STATUS_BLOCKED = "Blocked"
TASK_STATUS_DONE = "Done"
TASK_STATUS_CANCELLED = "Cancelled"

BLOCKING_TASK_STATUSES = frozenset(
	{
		TASK_STATUS_OPEN,
		TASK_STATUS_IN_PROGRESS,
		TASK_STATUS_BLOCKED,
	}
)

VALID_TASK_STATUSES = frozenset(
	{
		TASK_STATUS_OPEN,
		TASK_STATUS_IN_PROGRESS,
		TASK_STATUS_BLOCKED,
		TASK_STATUS_DONE,
		TASK_STATUS_CANCELLED,
	}
)


def normalize_task_title(title):
	return (title or "").strip().casefold()


def apply_status_transition(row, now=None):
	"""Set or clear completed_on based on task status."""
	now = now or now_datetime()
	if row.status == TASK_STATUS_DONE:
		if not row.completed_on:
			row.completed_on = now
	else:
		row.completed_on = None


def find_duplicate_open_tasks(rows):
	"""Return duplicate (task_title, assignee) keys among blocking-status rows."""
	seen = set()
	duplicates = set()

	for row in rows:
		if row.status not in BLOCKING_TASK_STATUSES:
			continue

		title = normalize_task_title(row.task_title)
		if not title or not row.assignee:
			continue

		key = (title, row.assignee)
		if key in seen:
			duplicates.add(key)
		else:
			seen.add(key)

	return duplicates


def get_blocking_tasks(rows):
	"""Return rows that block incident closure."""
	return [row for row in rows or [] if row.status in BLOCKING_TASK_STATUSES]


def format_blocking_tasks_message(blocking_tasks, max_display=5):
	"""Format blocking task titles for close-gate validation errors."""
	titles = [row.task_title for row in blocking_tasks if row.task_title]
	if not titles:
		return _("Cannot close incident with unresolved investigation tasks.")

	displayed = titles[:max_display]
	message = ", ".join(displayed)
	remaining = len(titles) - max_display
	if remaining > 0:
		message = f"{message}, ...and {remaining} more"

	return _("Cannot close incident with unresolved investigation tasks: {0}").format(message)


def validate_due_on(row, now=None):
	"""Reject past due dates for newly added task rows."""
	if not row.due_on:
		return

	now = get_datetime(now or now_datetime())
	due = get_datetime(row.due_on)
	if due >= now:
		return

	if getattr(row, "is_new", lambda: True)():
		frappe.throw(
			_("Due date cannot be in the past for new investigation task: {0}").format(row.task_title)
		)


def validate_investigation_task_rows(rows, now=None):
	"""Validate investigation task child rows on an incident."""
	if not rows:
		return

	now = now or now_datetime()

	for row in rows:
		if not row.task_title:
			frappe.throw(_("Task Title is required for each investigation task row."))

		if not row.assignee:
			frappe.throw(
				_("Assignee is required for investigation task: {0}").format(row.task_title)
			)

		if not row.status:
			frappe.throw(
				_("Status is required for investigation task: {0}").format(row.task_title)
			)

		if row.status not in VALID_TASK_STATUSES:
			frappe.throw(
				_("Invalid investigation task status for {0}: {1}").format(row.task_title, row.status)
			)

		apply_status_transition(row, now=now)
		validate_due_on(row, now=now)

	duplicates = find_duplicate_open_tasks(rows)
	if duplicates:
		labels = []
		for title, assignee in sorted(duplicates):
			labels.append(f"{title} ({assignee})")
		frappe.throw(
			_("Duplicate open investigation tasks are not allowed: {0}").format(", ".join(labels))
		)
