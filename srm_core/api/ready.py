"""Public readiness probe helpers (lightweight dependency checks)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import frappe


def _safe_fail_detail(exc: BaseException) -> str:
	"""Short non-sensitive detail for failed checks (no DSNs / stack traces)."""
	name = type(exc).__name__
	if name in {"TimeoutError", "ConnectionError", "OSError"}:
		return "unavailable"
	return "error"


def check_db() -> dict[str, str]:
	"""Lightweight DB connectivity check."""
	try:
		frappe.db.sql("select 1")
		return {"status": "ok"}
	except Exception as exc:
		return {"status": "fail", "detail": _safe_fail_detail(exc)}


def check_cache() -> dict[str, str]:
	"""Lightweight Redis/cache connectivity check."""
	try:
		cache = frappe.cache()
		ping = getattr(cache, "ping", None)
		if callable(ping):
			ping()
		else:
			# Fallback: round-trip a throwaway key on older cache APIs
			cache.set_value("srm_core:ready:ping", "1", expires_in_sec=5)
			cache.get_value("srm_core:ready:ping")
		return {"status": "ok"}
	except Exception as exc:
		return {"status": "fail", "detail": _safe_fail_detail(exc)}


def run_readiness_checks(
	*,
	db_check=check_db,
	cache_check=check_cache,
) -> dict[str, dict[str, str]]:
	"""Run required checks (injectable for tests)."""
	return {
		"db": db_check(),
		"cache": cache_check(),
	}


def build_ready_payload(
	*,
	db_check=check_db,
	cache_check=check_cache,
) -> tuple[dict[str, Any], int]:
	"""Return (payload, http_status) for GET /ready."""
	checks = run_readiness_checks(db_check=db_check, cache_check=cache_check)
	all_ok = all(item.get("status") == "ok" for item in checks.values())
	payload = {
		"status": "ready" if all_ok else "not_ready",
		"service": "srm-core",
		"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		"checks": checks,
	}
	return payload, (200 if all_ok else 503)


@frappe.whitelist(allow_guest=True)
def ready():
	"""Optional RPC alias for the readiness payload (HTTP status via GET /ready)."""
	payload, _status = build_ready_payload()
	return payload
