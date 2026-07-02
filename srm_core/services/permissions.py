"""Permission helpers for SRM Core."""

import frappe

IKS_PRIVILEGED_ROLES = frozenset({"SRM Admin", "System Manager"})

SRM_ROLES = (
	"SRM Admin",
	"SRM Case Manager",
	"SRM Analyst",
	"SRM Lead",
	"SRM Viewer",
)


def user_has_iks_privileged_role(user=None):
	user = user or frappe.session.user
	return bool(set(frappe.get_roles(user)) & IKS_PRIVILEGED_ROLES)


def user_has_system_manager_role(user=None):
	user = user or frappe.session.user
	return "System Manager" in frappe.get_roles(user)


def ensure_srm_roles():
	for role_name in SRM_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)
