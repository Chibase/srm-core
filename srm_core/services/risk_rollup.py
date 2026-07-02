"""Residual risk rollup and incident risk register linkage for SRM Core."""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from srm_core.services.escalation import ESCALATION_L1, ESCALATION_L2, ESCALATION_L3, ESCALATION_NONE
from srm_core.services.investigation_tasks import TASK_STATUS_CANCELLED, TASK_STATUS_DONE
from srm_core.services.permissions import user_has_system_manager_role
from srm_core.services.statuses import INCIDENT_CLOSED

RESIDUAL_BAND_LOW = "Low"
RESIDUAL_BAND_MODERATE = "Moderate"
RESIDUAL_BAND_HIGH = "High"
RESIDUAL_BAND_CRITICAL = "Critical"

ESCALATION_SCORE_MAP = {
	ESCALATION_NONE: 10,
	ESCALATION_L1: 30,
	ESCALATION_L2: 60,
	ESCALATION_L3: 90,
}


def compute_task_completion_ratio(tasks):
	"""Return Done / non-cancelled task ratio; 0.0 when no eligible tasks."""
	non_cancelled = [row for row in tasks or [] if row.status != TASK_STATUS_CANCELLED]
	if not non_cancelled:
		return 0.0
	done_count = sum(1 for row in non_cancelled if row.status == TASK_STATUS_DONE)
	return flt(done_count) / len(non_cancelled)


def compute_residual_risk_score(
	impact_score,
	priority_score,
	escalation_level,
	task_completion_ratio,
):
	"""Compute deterministic residual risk score (0-100, 2 decimal places)."""
	impact_component = flt(impact_score) * 0.35
	priority_component = flt(priority_score) * 0.35
	escalation_score = ESCALATION_SCORE_MAP.get(escalation_level or ESCALATION_NONE, 10)
	escalation_component = escalation_score * 0.20
	penalty_component = (1 - flt(task_completion_ratio)) * 100 * 0.10
	total = impact_component + priority_component + escalation_component + penalty_component
	score = flt(round(total, 2))
	return min(100.0, max(0.0, score))


def band_residual_risk(score):
	"""Map residual risk score to Low / Moderate / High / Critical bands."""
	value = flt(score)
	if value < 25:
		return RESIDUAL_BAND_LOW
	if value < 50:
		return RESIDUAL_BAND_MODERATE
	if value < 75:
		return RESIDUAL_BAND_HIGH
	return RESIDUAL_BAND_CRITICAL


def build_residual_rationale(
	impact_score,
	priority_score,
	escalation_level,
	task_completion_ratio,
	score,
	band,
):
	"""Build human-readable rationale for computed residual risk."""
	escalation_score = ESCALATION_SCORE_MAP.get(escalation_level or ESCALATION_NONE, 10)
	completion_pct = int(round(flt(task_completion_ratio) * 100))
	return _(
		"Residual risk {0} ({1}): impact {2}×35%, priority {3}×35%, "
		"escalation {4}→{5}×20%, task completion {6}% (penalty applied)."
	).format(
		score,
		band,
		flt(impact_score),
		flt(priority_score),
		escalation_level or ESCALATION_NONE,
		escalation_score,
		completion_pct,
	)


def linked_risk_changed(previous, current):
	previous_value = getattr(previous, "linked_risk", None) if previous else None
	current_value = current.linked_risk or None
	return bool(current_value) and current_value != previous_value


def residual_risk_materially_changed(previous, current):
	if not current.linked_risk:
		return False
	previous_score = flt(getattr(previous, "residual_risk_score", 0)) if previous else 0.0
	current_score = flt(current.residual_risk_score)
	previous_band = getattr(previous, "residual_risk_band", None) if previous else None
	if abs(current_score - previous_score) >= 0.01:
		return True
	return previous_band != current.residual_risk_band


def apply_incident_risk_linkage(doc, previous=None):
	"""Stamp risk link metadata and compute or clear residual risk fields."""
	previous_linked = getattr(previous, "linked_risk", None) if previous else None
	current_linked = doc.linked_risk or None

	if current_linked and current_linked != previous_linked:
		doc.risk_linked_on = now_datetime()
		doc.risk_linked_by = frappe.session.user

	if current_linked:
		completion_ratio = compute_task_completion_ratio(doc.investigation_tasks)
		score = compute_residual_risk_score(
			doc.impact_score,
			doc.priority_score,
			doc.escalation_level,
			completion_ratio,
		)
		band = band_residual_risk(score)
		doc.residual_risk_score = score
		doc.residual_risk_band = band
		doc.residual_risk_rationale = build_residual_rationale(
			doc.impact_score,
			doc.priority_score,
			doc.escalation_level,
			completion_ratio,
			score,
			band,
		)
	else:
		doc.residual_risk_score = 0.0
		doc.residual_risk_band = None
		doc.residual_risk_rationale = None

	if doc.name:
		_persist_incident_residual_risk(doc, previous)


def validate_residual_risk_close_gate(doc, previous=None):
	"""Block closure when linked risk remains at Critical residual band."""
	previous = previous or doc.get_doc_before_save()
	closing = doc.status == INCIDENT_CLOSED and (
		doc.is_new() or not previous or previous.status != INCIDENT_CLOSED
	)
	if not closing:
		return

	if doc.linked_risk and doc.residual_risk_band == RESIDUAL_BAND_CRITICAL:
		if not user_has_system_manager_role():
			frappe.throw(
				_(
					"Cannot close incident: residual risk is Critical while a risk register "
					"entry is linked. Reduce residual risk through mitigation or request "
					"System Manager override."
				)
			)


def touch_risk_register_with_incident(risk_name, incident_name, incident_title=None):
	"""Best-effort append of incident reference on linked risk register entry."""
	if not risk_name or not incident_name:
		return

	try:
		if not frappe.db.exists("DocType", "SRM Risk Register"):
			return
		if not frappe.db.exists("SRM Risk Register", risk_name):
			return

		meta = frappe.get_meta("SRM Risk Register")
		note_field = None
		for candidate in ("incident_references", "notes", "description"):
			if meta.has_field(candidate):
				note_field = candidate
				break
		if not note_field:
			return

		title = incident_title or incident_name
		line = f"[{now_datetime()}] Linked incident {incident_name}: {title}"
		current = frappe.db.get_value("SRM Risk Register", risk_name, note_field) or ""
		if incident_name in current:
			return

		updated = f"{current}\n{line}".strip() if current else line
		frappe.db.set_value(
			"SRM Risk Register",
			risk_name,
			note_field,
			updated,
			update_modified=False,
		)
	except Exception:
		frappe.logger("srm_core").warning(
			"Failed to update risk register reference for incident %s -> risk %s",
			incident_name,
			risk_name,
			exc_info=True,
		)


def _persist_incident_residual_risk(doc, previous=None):
	previous_linked = getattr(previous, "linked_risk", None) if previous else None
	current_linked = doc.linked_risk or None
	if not current_linked and not previous_linked:
		return

	if current_linked:
		doc.db_set("residual_risk_score", doc.residual_risk_score, update_modified=False)
		doc.db_set("residual_risk_band", doc.residual_risk_band, update_modified=False)
		doc.db_set("residual_risk_rationale", doc.residual_risk_rationale, update_modified=False)
		doc.db_set("risk_linked_on", doc.risk_linked_on, update_modified=False)
		doc.db_set("risk_linked_by", doc.risk_linked_by, update_modified=False)
		return

	doc.db_set("residual_risk_score", 0, update_modified=False)
	doc.db_set("residual_risk_band", "", update_modified=False)
	doc.db_set("residual_risk_rationale", "", update_modified=False)
