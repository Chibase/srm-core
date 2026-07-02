"""Incident attachment helpers and evidence controls for SRM Core."""

import hashlib
import os

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from srm_core.services.permissions import user_has_system_manager_role
from srm_core.services.statuses import INCIDENT_CLOSED

VALID_EVIDENCE_TYPES = frozenset(
	{"screenshot", "document", "audio", "video", "log", "other"}
)
VALID_CLASSIFICATIONS = frozenset(
	{"public", "internal", "confidential", "restricted"}
)
SENSITIVE_CLASSIFICATIONS = frozenset({"confidential", "restricted"})


def compute_integrity_hash(content_bytes):
	"""Return SHA256 hex digest for attachment content bytes."""
	if content_bytes is None:
		return None
	if isinstance(content_bytes, str):
		content_bytes = content_bytes.encode()
	return hashlib.sha256(content_bytes).hexdigest()


def normalize_file_name(file_url):
	"""Best-effort file name extraction from a Frappe file URL/path."""
	if not file_url:
		return ""
	clean = str(file_url).split("?")[0].replace("\\", "/").strip()
	return os.path.basename(clean) or clean


def validate_single_primary_evidence(rows):
	"""Ensure at most one active primary evidence attachment exists."""
	primary_count = sum(
		1
		for row in rows or []
		if cint(row.is_primary_evidence) and not cint(row.is_removed)
	)
	if primary_count > 1:
		frappe.throw(_("Only one active primary evidence attachment is allowed."))


def apply_removal_transition(row, previous_row, now=None, user=None):
	"""Apply soft-remove or restore semantics for an attachment row."""
	now = now or now_datetime()
	user = user or frappe.session.user

	if not previous_row:
		if cint(row.is_removed):
			frappe.throw(_("New attachments cannot be created as removed."))
		return

	was_removed = cint(previous_row.is_removed)
	is_removed = cint(row.is_removed)

	if not was_removed and is_removed:
		if not (row.removal_reason or "").strip():
			frappe.throw(_("Removal reason is required when removing attachment evidence."))
		row.removed_on = now
		row.removed_by = user
	elif was_removed and not is_removed:
		if not user_has_system_manager_role():
			frappe.throw(_("Only System Manager can restore removed attachments."))
		row.removed_on = None
		row.removed_by = None
		row.removal_reason = None


def validate_closed_incident_attachment_changes(rows, previous_rows, incident_status):
	"""Block add/remove attachment changes on closed incidents for non-admins."""
	if incident_status != INCIDENT_CLOSED or user_has_system_manager_role():
		return

	previous_by_name = {row.name: row for row in (previous_rows or []) if row.name}
	for row in rows or []:
		is_new_row = getattr(row, "is_new", lambda: True)() or not row.name or row.name not in previous_by_name
		if is_new_row:
			frappe.throw(_("Cannot add attachments to a closed incident."))

		previous = previous_by_name.get(row.name)
		if previous and cint(previous.is_removed) != cint(row.is_removed):
			frappe.throw(_("Cannot add or remove attachments on a closed incident."))


def validate_incident_attachment_rows(rows, previous_rows=None, incident_status=None):
	"""Validate and stamp incident attachment child rows."""
	if not rows:
		return

	previous_by_name = {row.name: row for row in (previous_rows or []) if row.name}
	now = now_datetime()
	user = frappe.session.user

	validate_closed_incident_attachment_changes(rows, previous_rows, incident_status)

	for row in rows:
		if not row.file_url:
			frappe.throw(_("File URL is required for each attachment row."))
		if not row.file_name:
			row.file_name = normalize_file_name(row.file_url)
		if not row.file_name:
			frappe.throw(_("File Name is required for each attachment row."))
		if not row.evidence_type:
			frappe.throw(_("Evidence Type is required for attachment: {0}").format(row.file_name))
		if row.evidence_type not in VALID_EVIDENCE_TYPES:
			frappe.throw(_("Invalid evidence type for attachment: {0}").format(row.file_name))
		if not row.classification:
			frappe.throw(_("Classification is required for attachment: {0}").format(row.file_name))
		if row.classification not in VALID_CLASSIFICATIONS:
			frappe.throw(_("Invalid classification for attachment: {0}").format(row.file_name))

		is_new_row = getattr(row, "is_new", lambda: True)() or not row.name or row.name not in previous_by_name
		if is_new_row:
			row.attached_on = row.attached_on or now
			row.attached_by = row.attached_by or user

		previous = previous_by_name.get(row.name)
		apply_removal_transition(row, previous, now=now, user=user)

	validate_single_primary_evidence(rows)


def diff_incident_attachments(previous_rows, current_rows):
	"""Return newly added attachments and rows soft-removed in this save."""
	previous_rows = previous_rows or []
	current_rows = current_rows or []
	previous_by_name = {row.name: row for row in previous_rows if row.name}

	added = []
	removed = []
	for row in current_rows:
		if not row.name or row.name not in previous_by_name:
			added.append(row)
			continue
		previous = previous_by_name[row.name]
		if not cint(previous.is_removed) and cint(row.is_removed):
			removed.append(row)
	return added, removed


def get_incident_attachments(
	incident_name,
	include_removed=False,
	classification=None,
	limit=200,
):
	"""Return incident attachments ordered newest first.

	Callers must enforce authorization before invoking this helper, for example::

	    frappe.has_permission("SRM Incident", "read", incident_name, throw=True)
	    attachments = get_incident_attachments(incident_name)
	"""
	filters = {
		"parent": incident_name,
		"parenttype": "SRM Incident",
		"parentfield": "attachments",
	}
	if not include_removed:
		filters["is_removed"] = 0
	if classification:
		filters["classification"] = classification

	return frappe.get_all(
		"SRM Incident Attachment",
		filters=filters,
		fields=[
			"name",
			"file_url",
			"file_name",
			"attached_on",
			"attached_by",
			"evidence_type",
			"classification",
			"integrity_hash",
			"notes",
			"is_primary_evidence",
			"is_removed",
			"removed_on",
			"removed_by",
			"removal_reason",
		],
		order_by="attached_on desc, idx desc",
		limit=limit,
	)
