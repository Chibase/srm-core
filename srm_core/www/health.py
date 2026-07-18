"""GET /health — public liveness probe (JSON, no-cache, guest-safe)."""

from __future__ import annotations

import json

from frappe.website.page_renderers.base_renderer import BaseRenderer
from werkzeug.wrappers import Response

from srm_core.api.health import build_health_payload

no_cache = 1
sitemap = 0


class HealthPageRenderer(BaseRenderer):
	"""Serve exact JSON body at GET /health without HTML wrapping."""

	def can_render(self):
		return self.path.strip("/") == "health"

	def render(self):
		return Response(
			json.dumps(build_health_payload()),
			status=200,
			content_type="application/json; charset=utf-8",
			headers={"Cache-Control": "no-store"},
		)
