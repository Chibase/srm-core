"""GET /ready — public readiness probe (JSON, no-cache, guest-safe)."""

from __future__ import annotations

import json

from frappe.website.page_renderers.base_renderer import BaseRenderer
from werkzeug.wrappers import Response

from srm_core.api.ready import build_ready_payload

no_cache = 1
sitemap = 0


class ReadyPageRenderer(BaseRenderer):
	"""Serve exact JSON body at GET /ready without HTML wrapping."""

	def can_render(self):
		return self.path.strip("/") == "ready"

	def render(self):
		payload, http_status = build_ready_payload()
		return Response(
			json.dumps(payload),
			status=http_status,
			content_type="application/json; charset=utf-8",
			headers={"Cache-Control": "no-store"},
		)
