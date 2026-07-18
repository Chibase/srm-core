# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from srm_core.api.ready import build_ready_payload, ready


class TestReady(FrappeTestCase):
	def test_ready_when_dependencies_ok(self):
		payload, status = build_ready_payload(
			db_check=lambda: {"status": "ok"},
			cache_check=lambda: {"status": "ok"},
		)
		self.assertEqual(status, 200)
		self.assertEqual(payload["status"], "ready")
		self.assertEqual(payload["service"], "srm-core")
		self.assertEqual(set(payload.keys()), {"status", "service", "timestamp", "checks"})
		self.assertEqual(set(payload["checks"].keys()), {"db", "cache"})
		self.assertEqual(payload["checks"]["db"]["status"], "ok")
		self.assertEqual(payload["checks"]["cache"]["status"], "ok")
		normalized = payload["timestamp"].replace("Z", "+00:00")
		datetime.fromisoformat(normalized)

	def test_not_ready_when_db_fails(self):
		payload, status = build_ready_payload(
			db_check=lambda: {"status": "fail", "detail": "unavailable"},
			cache_check=lambda: {"status": "ok"},
		)
		self.assertEqual(status, 503)
		self.assertEqual(payload["status"], "not_ready")
		self.assertEqual(payload["checks"]["db"]["status"], "fail")
		self.assertEqual(payload["checks"]["cache"]["status"], "ok")

	def test_not_ready_when_cache_fails(self):
		payload, status = build_ready_payload(
			db_check=lambda: {"status": "ok"},
			cache_check=lambda: {"status": "fail", "detail": "unavailable"},
		)
		self.assertEqual(status, 503)
		self.assertEqual(payload["status"], "not_ready")
		self.assertEqual(payload["checks"]["db"]["status"], "ok")
		self.assertEqual(payload["checks"]["cache"]["status"], "fail")

	def test_ready_whitelist_guest_safe(self):
		frappe.set_user("Guest")
		with patch("srm_core.api.ready.check_db", return_value={"status": "ok"}), patch(
			"srm_core.api.ready.check_cache", return_value={"status": "ok"}
		):
			payload = ready()
		self.assertEqual(payload["status"], "ready")
		self.assertEqual(payload["service"], "srm-core")

	def test_get_ready_http_ok(self):
		from frappe.website.serve import get_response

		frappe.set_user("Guest")
		with patch("srm_core.api.ready.check_db", return_value={"status": "ok"}), patch(
			"srm_core.api.ready.check_cache", return_value={"status": "ok"}
		):
			response = get_response("/ready")
		self.assertEqual(response.status_code, 200)
		self.assertIn("application/json", response.headers.get("Content-Type", ""))
		data = json.loads(response.get_data(as_text=True))
		self.assertEqual(data["status"], "ready")
		self.assertEqual(data["checks"]["db"]["status"], "ok")
		self.assertEqual(data["checks"]["cache"]["status"], "ok")

	def test_get_ready_http_not_ready_db(self):
		from frappe.website.serve import get_response

		frappe.set_user("Guest")
		with patch(
			"srm_core.api.ready.check_db",
			return_value={"status": "fail", "detail": "unavailable"},
		), patch("srm_core.api.ready.check_cache", return_value={"status": "ok"}):
			response = get_response("/ready")
		self.assertEqual(response.status_code, 503)
		data = json.loads(response.get_data(as_text=True))
		self.assertEqual(data["status"], "not_ready")
		self.assertEqual(data["checks"]["db"]["status"], "fail")

	def test_get_ready_http_not_ready_cache(self):
		from frappe.website.serve import get_response

		frappe.set_user("Guest")
		with patch("srm_core.api.ready.check_db", return_value={"status": "ok"}), patch(
			"srm_core.api.ready.check_cache",
			return_value={"status": "fail", "detail": "cache unavailable"},
		):
			response = get_response("/ready")
		self.assertEqual(response.status_code, 503)
		payload = json.loads(response.get_data(as_text=True))
		self.assertEqual(payload["status"], "not_ready")
		self.assertIn("checks", payload)
		self.assertEqual(payload["checks"]["cache"]["status"], "fail")
