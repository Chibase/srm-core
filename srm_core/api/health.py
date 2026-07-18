"""Public health / liveness probe helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import frappe


def build_health_payload() -> dict[str, str]:
	"""Return the GET /health JSON contract (no I/O, no auth)."""
	return {
		"status": "ok",
		"service": "srm-core",
		"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
	}


@frappe.whitelist(allow_guest=True)
def health():
	"""Optional RPC alias for the liveness payload.

	Primary probe path is GET /health (see srm_core.www.health).
	"""
	return build_health_payload()
