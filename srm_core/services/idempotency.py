"""Shared idempotency helpers for SRM Core."""

import hashlib

import frappe
from frappe.utils import cstr

LOGGER = frappe.logger("srm_core")


def is_duplicate_entry_error(exc):
	"""Return True when exception represents a unique/idempotency key conflict."""
	if isinstance(exc, frappe.DuplicateEntryError):
		return True

	message = cstr(getattr(exc, "args", [""])[0]).lower()
	return "duplicate" in message or "1062" in message or "unique" in message


def get_existing_name_by_idempotency_key(doctype, idempotency_key):
	"""Return document name for an idempotency key when present."""
	if not idempotency_key:
		return None
	return frappe.db.get_value(doctype, {"idempotency_key": idempotency_key}, "name")


def safe_doc_insert(doc, *, doctype, idempotency_key=None, context=None):
	"""Insert a document, gracefully skipping duplicate idempotency conflicts."""
	if idempotency_key:
		existing = get_existing_name_by_idempotency_key(doctype, idempotency_key)
		if existing:
			return None

	try:
		doc.insert(ignore_permissions=True)
		return doc
	except Exception as exc:
		if is_duplicate_entry_error(exc):
			LOGGER.warning(
				"Skipped duplicate %s insert for idempotency_key=%s context=%s",
				doctype,
				idempotency_key,
				context,
			)
			return None
		raise


def fallback_idempotency_key(*parts):
	"""Build deterministic fallback idempotency key from ordered parts."""
	payload = "|".join(cstr(part) for part in parts if part is not None)
	return hashlib.sha256(payload.encode()).hexdigest()
