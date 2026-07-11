"""TrustLedger session / auth helpers (whitelisted)."""

from __future__ import annotations

import frappe
from frappe import _


ROLE_PRIORITY = (
	("admin", ("System Manager", "SRM Admin")),
	("client", ("SRM Lead", "SRM Case Manager")),
	("contractor", ("SRM Analyst",)),
)


def map_trustledger_role(roles: list[str] | set[str] | None) -> str:
	"""Map Frappe roles to TrustLedger UserRole."""
	role_set = set(roles or [])
	for trust_role, frappe_roles in ROLE_PRIORITY:
		if role_set.intersection(frappe_roles):
			return trust_role
	return "community"


@frappe.whitelist()
def get_session():
	"""Return TrustLedger session context for the logged-in user."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not logged in"), frappe.PermissionError)

	roles = frappe.get_roles(frappe.session.user)
	full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user

	return {
		"user": frappe.session.user,
		"fullName": full_name,
		"roles": roles,
		"trustLedgerRole": map_trustledger_role(roles),
	}
