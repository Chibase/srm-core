# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from datetime import datetime

import frappe
from frappe.tests.utils import FrappeTestCase

from srm_core.api.health import build_health_payload, health


class TestHealth(FrappeTestCase):
	def test_build_health_payload_shape_and_values(self):
		payload = build_health_payload()
		self.assertEqual(set(payload.keys()), {"status", "service", "timestamp"})
		self.assertEqual(payload["status"], "ok")
		self.assertEqual(payload["service"], "srm-core")
		self.assertIsInstance(payload["status"], str)
		self.assertIsInstance(payload["service"], str)
		self.assertIsInstance(payload["timestamp"], str)
		self.assertTrue(payload["timestamp"])
		# Accept trailing Z or numeric offset
		normalized = payload["timestamp"].replace("Z", "+00:00")
		datetime.fromisoformat(normalized)

	def test_health_payload_guest_safe(self):
		frappe.set_user("Guest")
		payload = health()
		self.assertEqual(payload["status"], "ok")
		self.assertEqual(payload["service"], "srm-core")
		self.assertIn("timestamp", payload)

	def test_get_health_http(self):
		from frappe.website.serve import get_response

		frappe.set_user("Guest")
		response = get_response("/health")
		self.assertEqual(response.status_code, 200)
		content_type = response.headers.get("Content-Type", "")
		self.assertIn("application/json", content_type)
		data = json.loads(response.get_data(as_text=True))
		self.assertEqual(data["status"], "ok")
		self.assertEqual(data["service"], "srm-core")
		self.assertIsInstance(data["timestamp"], str)
		self.assertTrue(data["timestamp"])
