"""TrustLedger engagement / meeting-note API (whitelisted)."""

from __future__ import annotations

import frappe


@frappe.whitelist()
def list_meeting_notes(ward=None, projectId=None):
	"""Return meeting notes for TrustLedger.

	Engagement DocType is not yet implemented; returns an empty list so the
	frontend live mode degrades cleanly until Packet Engagement lands.
	"""
	frappe.has_permission("SRM Incident", "read", throw=True)
	# Reserved filters for future Engagement DocType
	_ = (ward, projectId)
	return []
