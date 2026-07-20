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


def ensure_pilot_user(email: str = "pilot@trustledger.co.za", password: str | None = None):
	"""Ops helper: create/enable a TrustLedger pilot user with SRM Admin.

	Not whitelisted — call via: bench execute srm_core.api.auth.ensure_pilot_user
	"""
	from frappe.utils.password import update_password

	if not password:
		password = frappe.generate_hash(length=12)

	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		user.enabled = 1
		user.save(ignore_permissions=True)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "TrustLedger",
				"last_name": "Pilot",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)

	user.add_roles("SRM Admin", "System Manager")
	update_password(email, password)
	frappe.db.commit()
	return {"email": email, "password": password, "roles": frappe.get_roles(email)}
