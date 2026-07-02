import frappe

from srm_core.services.permissions import ensure_srm_roles


def execute():
	ensure_srm_roles()
