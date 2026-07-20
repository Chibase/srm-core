"""Serialize SRM Core DocTypes into TrustLedger frontend DTOs."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, get_datetime

from srm_core.services.statuses import (
	INCIDENT_CLOSED,
	INCIDENT_RESOLVED,
	INCIDENT_UNDER_INVESTIGATION,
)

PROMPT_VERSION = "srm-ai-v0"
MODEL_HEURISTIC = "srm-heuristic-v0"


def _iso(value) -> str | None:
	if not value:
		return None
	try:
		return get_datetime(value).isoformat()
	except Exception:
		return str(value)


def map_incident_status(doc: Any) -> str:
	status = (doc.get("status") if isinstance(doc, dict) else doc.status) or "Open"
	is_escalated = cint(doc.get("is_escalated") if isinstance(doc, dict) else getattr(doc, "is_escalated", 0))
	if status in (INCIDENT_RESOLVED, INCIDENT_CLOSED):
		return "Closed"
	if is_escalated:
		return "Escalated"
	if status == INCIDENT_UNDER_INVESTIGATION:
		return "Investigating"
	return "Open"


def map_classification(value: str | None) -> str:
	raw = (value or "internal").lower()
	if raw in {"confidential"}:
		return "Confidential"
	if raw in {"restricted"}:
		return "Restricted"
	return "General"


def geographic_label(doc: Any) -> str:
	area = doc.get("geographic_area") if isinstance(doc, dict) else getattr(doc, "geographic_area", None)
	legacy = (
		doc.get("geographic_area_text")
		if isinstance(doc, dict)
		else getattr(doc, "geographic_area_text", None)
	)
	if area:
		try:
			title = frappe.db.get_value("Geographic Area", area, "area_name") or area
			return str(title)
		except Exception:
			return str(area)
	return str(legacy or "")


def serialize_timeline(incident_name: str) -> list[dict]:
	rows = frappe.get_all(
		"SRM Incident Event",
		filters={"incident": incident_name},
		fields=["name", "event_type", "summary", "event_time", "creation"],
		order_by="event_time asc, creation asc",
		limit_page_length=100,
	)
	out = []
	for row in rows:
		out.append(
			{
				"id": row.name,
				"type": row.event_type or "EVENT",
				"summary": row.summary or row.event_type or "",
				"at": _iso(row.event_time or row.creation) or "",
			}
		)
	return out


def latest_sentiment_score(incident_name: str, geographic_area: str | None) -> float | None:
	linked = frappe.get_all(
		"SRM Sentiment Capture",
		filters={"linked_incident": incident_name},
		fields=["sentiment_score"],
		order_by="capture_date desc, creation desc",
		limit_page_length=1,
	)
	if linked:
		return flt(linked[0].sentiment_score)

	if geographic_area:
		fallback = frappe.get_all(
			"SRM Sentiment Capture",
			filters={"geographic_area": geographic_area},
			fields=["sentiment_score"],
			order_by="capture_date desc, creation desc",
			limit_page_length=1,
		)
		if fallback:
			return flt(fallback[0].sentiment_score)
	return None


def serialize_incident(doc: Any, include_timeline: bool = True) -> dict:
	data = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)
	name = data.get("name")
	project = data.get("project") or ""
	owner = data.get("incident_owner") or ""
	owner_name = owner
	if owner:
		owner_name = frappe.db.get_value("User", owner, "full_name") or owner

	geo = geographic_label(data)
	payload = {
		"id": name,
		"title": data.get("incident_title") or name,
		"description": data.get("description") or "",
		"ward": geo,
		"geographicArea": geo,
		"status": map_incident_status(data),
		"priority": data.get("priority_level") or "P4-Low",
		"projectId": project or "UNASSIGNED",
		"projectName": project or "Unassigned project",
		"reportedByRole": "admin",
		"reportedAt": _iso(data.get("creation") or data.get("incident_date")) or "",
		"slaDueBy": _iso(data.get("sla_due_by") or data.get("sla_due_date")) or "",
		"slaBreached": bool(cint(data.get("sla_breached"))),
		"escalationLevel": data.get("escalation_level") or "None",
		"ownerName": owner_name or "Unassigned",
		"category": data.get("incident_channel") or "Other",
		"impactScore": flt(data.get("impact_score")),
		"sentimentScore": latest_sentiment_score(name, data.get("geographic_area")),
		"timeline": serialize_timeline(name) if include_timeline and name else [],
	}
	return payload


def serialize_evidence_row(row: Any, incident_name: str) -> dict | None:
	data = row.as_dict() if hasattr(row, "as_dict") else dict(row)
	if cint(data.get("is_removed")):
		return None
	classification = map_classification(data.get("classification"))
	return {
		"id": data.get("name") or f"{incident_name}-{data.get('file_name')}",
		"incidentId": incident_name,
		"fileName": data.get("file_name") or "file",
		"classification": classification,
		"uploadedBy": data.get("attached_by") or "system",
		"uploadedAt": _iso(data.get("attached_on") or data.get("creation")) or "",
		"isPrimary": bool(cint(data.get("is_primary_evidence"))),
	}


def serialize_project_stub(project_key: str, sample: dict | None = None) -> dict:
	sample = sample or {}
	return {
		"id": project_key,
		"name": project_key,
		"clientFunder": sample.get("programme") or "Programme funder",
		"budgetTotal": 0,
		"budgetSpent": 0,
		"ward": sample.get("ward") or "",
		"municipality": "",
		"status": "Active",
		"contractorName": "",
		"startDate": "",
		"targetEndDate": "",
		"publicSummary": f"Project stub derived from SRM Incident.project={project_key}",
	}
