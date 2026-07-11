"""TrustLedger AI assist API (whitelisted).

Default implementation is deterministic heuristics (no external network).
When Site Config / env provides an xAI key, callers can later swap to Grok.
"""

from __future__ import annotations

import frappe
from frappe import _

from srm_core.api.serializers import MODEL_HEURISTIC, PROMPT_VERSION


def _text(value) -> str:
	return (value or "").strip()


@frappe.whitelist()
def suggest_triage(description=None, ward=None, projectId=None, preferredLanguage=None):
	"""Return triage suggestion DTO for TrustLedger intake."""
	frappe.only_for(("System Manager", "SRM Admin", "SRM Case Manager", "SRM Analyst"))
	text = _text(description).lower()
	if not text:
		frappe.throw(_("description is required"))

	category = "General grievance"
	suggested_priority = "P3-Medium"
	impact_hints = ["Community relations"]

	if any(token in text for token in ("water", "pipe", "leak", "flood")):
		category = "Water / utilities disruption"
		suggested_priority = "P2-High"
		impact_hints.extend(["Livelihood access", "Service delivery"])
	elif any(token in text for token in ("safety", "injury", "accident", "danger", "road", "trench")):
		category = "Safety / access hazard"
		suggested_priority = "P1-Critical"
		impact_hints.extend(["Public safety", "Reputation"])
	elif any(token in text for token in ("noise", "dust", "blast")):
		category = "Construction nuisance"
		suggested_priority = "P3-Medium"
		impact_hints.extend(["Amenity", "Health & wellbeing"])

	summary = _text(description)[:140] or "Community-reported concern requiring triage."
	return {
		"summary": summary,
		"category": category,
		"geographicAreaHint": ward or "",
		"suggestedPriority": suggested_priority,
		"impactHints": impact_hints,
		"languageDetected": preferredLanguage or "en",
		"translatedDescription": None,
		"confidence": 0.78,
		"model": MODEL_HEURISTIC,
		"promptVersion": PROMPT_VERSION,
	}


@frappe.whitelist()
def suggest_sentiment(text=None, geographicArea=None, linkedIncidentId=None, sourceType=None):
	"""Return sentiment suggestion DTO."""
	frappe.only_for(("System Manager", "SRM Admin", "SRM Case Manager", "SRM Analyst"))
	body = _text(text).lower()
	if not body:
		frappe.throw(_("text is required"))

	score = -20
	if any(token in body for token in ("angry", "furious", "threat", "protest", "unsafe")):
		score = -75
	elif any(token in body for token in ("concern", "worried", "delay", "broken")):
		score = -45
	elif any(token in body for token in ("thank", "appreciate", "resolved", "good")):
		score = 55

	return {
		"sentimentScore": score,
		"confidenceScore": 0.72,
		"rationale": "Heuristic intensity estimate from wording cues.",
		"sourceType": sourceType or "Other",
		"model": MODEL_HEURISTIC,
		"promptVersion": PROMPT_VERSION,
	}


@frappe.whitelist()
def draft_response(incidentId=None, description=None, audience=None, language=None):
	"""Return community/client response draft."""
	frappe.only_for(("System Manager", "SRM Admin", "SRM Case Manager", "SRM Analyst"))
	_ = description
	audience = audience or "community"
	tone = "empathetic" if audience == "community" else "formal"
	draft = (
		"Thank you for raising this concern about the project in your area.\n\n"
		"We have logged your report and assigned it for review. Our team will investigate "
		"and share an update within the applicable response window.\n\n"
		"If you have photos, meeting references, or additional details, please reply so we "
		"can attach them to the case record.\n\n"
		"TrustLedger Community Desk"
	)
	if incidentId:
		draft = f"[Ref {incidentId}]\n\n" + draft

	return {
		"draft": draft,
		"tone": tone,
		"language": language or "en",
		"model": MODEL_HEURISTIC,
		"promptVersion": PROMPT_VERSION,
	}


@frappe.whitelist()
def generate_report_brief(projectId=None, incidentIds=None, audience=None):
	"""Return governance brief draft from open incidents."""
	frappe.only_for(("System Manager", "SRM Admin", "SRM Analyst", "SRM Case Manager"))
	audience = audience or "board"

	filters = {}
	if projectId:
		filters["project"] = projectId

	names = incidentIds
	if isinstance(names, str):
		# Frappe may pass JSON string
		try:
			import json

			parsed = json.loads(names)
			if isinstance(parsed, list):
				names = parsed
		except Exception:
			names = [names]

	if not names:
		names = frappe.get_all(
			"SRM Incident",
			filters=filters,
			pluck="name",
			order_by="modified desc",
			limit_page_length=10,
		)

	cited = list(names or [])
	return {
		"title": f"Stakeholder risk brief ({audience})",
		"executiveSummary": (
			"Open community concerns remain concentrated around service disruption and site access. "
			"Priority scoring blends impact taxonomy with recent sentiment captures. "
			"This draft is for human review before board circulation."
		),
		"keyRisks": [
			"Unresolved high-priority incidents near active wards",
			"Sentiment intensity elevating SLA pressure",
			"Evidence gaps on critical residual-risk cases",
		],
		"recommendedActions": [
			"Confirm owners and investigation tasks on P1/P2 incidents",
			"Link latest community meeting notes to sentiment captures",
			"Prepare assurance pack with timeline citations",
		],
		"citedIncidentIds": cited,
		"model": MODEL_HEURISTIC,
		"promptVersion": PROMPT_VERSION,
	}
