"""Escalation policy and assignment enforcement helpers for SRM Core."""

import frappe
from frappe import _

from srm_core.services.investigation_tasks import (
	TASK_STATUS_BLOCKED,
	TASK_STATUS_DONE,
	TASK_STATUS_IN_PROGRESS,
	TASK_STATUS_OPEN,
)
from srm_core.services.priority import (
	PRIORITY_P1_CRITICAL,
	PRIORITY_P2_HIGH,
	PRIORITY_P3_MEDIUM,
)

ESCALATION_NONE = "None"
ESCALATION_L1 = "L1"
ESCALATION_L2 = "L2"
ESCALATION_L3 = "L3"

AUTO_REASON_PREFIX = "[AUTO]"

IMPACT_BAND_CRITICAL = "Critical"

ESCALATION_LEVEL_RANK = {
	ESCALATION_NONE: 0,
	ESCALATION_L1: 1,
	ESCALATION_L2: 2,
	ESCALATION_L3: 3,
}

ASSIGNMENT_REQUIRED_PRIORITIES = frozenset({PRIORITY_P1_CRITICAL, PRIORITY_P2_HIGH})

ACCOUNTABLE_TASK_STATUSES = frozenset(
	{
		TASK_STATUS_OPEN,
		TASK_STATUS_IN_PROGRESS,
		TASK_STATUS_BLOCKED,
		TASK_STATUS_DONE,
	}
)


def is_auto_escalation_reason(reason):
	return bool(reason and str(reason).startswith(AUTO_REASON_PREFIX))


def derive_escalation_level(priority_level, impact_band, requires_exec, is_sla_breached):
	"""Derive escalation level; highest matching rule wins."""
	if priority_level == PRIORITY_P1_CRITICAL:
		return ESCALATION_L3
	if impact_band == IMPACT_BAND_CRITICAL:
		return ESCALATION_L3
	if requires_exec:
		return ESCALATION_L3

	if priority_level == PRIORITY_P2_HIGH:
		return ESCALATION_L2
	if is_sla_breached:
		return ESCALATION_L2

	if priority_level == PRIORITY_P3_MEDIUM:
		return ESCALATION_L1

	return ESCALATION_NONE


def build_auto_escalation_reason(
	level,
	priority_level,
	is_sla_breached,
	impact_band,
	requires_exec=False,
):
	"""Build deterministic auto-generated escalation reason text."""
	if level == ESCALATION_NONE:
		return None

	triggers = []
	if level == ESCALATION_L3:
		if priority_level == PRIORITY_P1_CRITICAL:
			triggers.append(f"priority {priority_level}")
		if impact_band == IMPACT_BAND_CRITICAL:
			triggers.append(f"impact band {impact_band}")
		if requires_exec:
			triggers.append("executive attention required")
	elif level == ESCALATION_L2:
		if priority_level == PRIORITY_P2_HIGH:
			triggers.append(f"priority {priority_level}")
		if is_sla_breached:
			triggers.append("SLA breach")
	elif level == ESCALATION_L1:
		if priority_level == PRIORITY_P3_MEDIUM:
			triggers.append(f"priority {priority_level}")

	trigger_text = " and ".join(triggers) if triggers else "policy match"
	return f"{AUTO_REASON_PREFIX} Auto-escalated to {level} due to {trigger_text}."


def resolve_escalation_reason(
	current_reason,
	level,
	priority_level,
	is_sla_breached,
	impact_band,
	requires_exec=False,
):
	"""Preserve manual reasons; manage auto-generated reason lifecycle."""
	if level == ESCALATION_NONE:
		if is_auto_escalation_reason(current_reason):
			return None
		return current_reason or None

	if current_reason and not is_auto_escalation_reason(current_reason):
		return current_reason

	return build_auto_escalation_reason(
		level,
		priority_level,
		is_sla_breached,
		impact_band,
		requires_exec=requires_exec,
	)


def should_refresh_escalation_stamp(previous_level, new_level, was_escalated, is_escalated):
	"""Refresh escalation audit stamp on first escalate or level increase."""
	if not is_escalated:
		return False
	if not was_escalated:
		return True

	previous_rank = ESCALATION_LEVEL_RANK.get(previous_level or ESCALATION_NONE, 0)
	new_rank = ESCALATION_LEVEL_RANK.get(new_level or ESCALATION_NONE, 0)
	return new_rank > previous_rank


def has_accountable_investigation_task(rows):
	"""Return True when at least one task has assignee and accountable status."""
	for row in rows or []:
		if row.status in ACCOUNTABLE_TASK_STATUSES and row.assignee:
			return True
	return False


def validate_high_priority_assignment(priority_level, incident_owner, investigation_tasks):
	"""Enforce owner and task assignment for P1/P2 incidents."""
	if priority_level not in ASSIGNMENT_REQUIRED_PRIORITIES:
		return

	if not incident_owner:
		frappe.throw(
			_(
				"Incident Owner is required for {0} incidents. Assign an owner before saving."
			).format(priority_level)
		)

	if not has_accountable_investigation_task(investigation_tasks):
		frappe.throw(
			_(
				"At least one investigation task with an assignee is required for {0} "
				"incidents (status Open, In Progress, Blocked, or Done)."
			).format(priority_level)
		)
