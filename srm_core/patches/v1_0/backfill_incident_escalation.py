import frappe
from frappe.utils import cint, now_datetime

from srm_core.services.escalation import (
	ESCALATION_NONE,
	derive_escalation_level,
	resolve_escalation_reason,
)


def execute():
	updated = 0
	now = now_datetime()

	for row in frappe.get_all(
		"SRM Incident",
		fields=[
			"name",
			"priority_level",
			"impact_band",
			"requires_executive_attention",
			"sla_breached",
			"escalation_level",
			"escalation_reason",
			"is_escalated",
		],
	):
		requires_exec = cint(row.requires_executive_attention)
		is_sla_breached = cint(row.sla_breached)
		level = derive_escalation_level(
			row.priority_level or "",
			row.impact_band or "",
			requires_exec,
			is_sla_breached,
		)
		is_escalated = cint(level != ESCALATION_NONE)
		reason = resolve_escalation_reason(
			row.escalation_reason,
			level,
			row.priority_level or "",
			is_sla_breached,
			row.impact_band or "",
			requires_exec=requires_exec,
		)

		if (
			(row.escalation_level or ESCALATION_NONE) == level
			and cint(row.is_escalated) == is_escalated
			and (row.escalation_reason or None) == (reason or None)
		):
			continue

		values = {
			"is_escalated": is_escalated,
			"escalation_level": level,
			"escalation_reason": reason,
		}
		if is_escalated and not row.escalation_level:
			values["escalated_on"] = now
			values["escalated_by"] = "Administrator"

		frappe.db.set_value("SRM Incident", row.name, values, update_modified=False)
		updated += 1

	frappe.db.commit()
	summary = f"Incident escalation backfill: updated={updated}"
	frappe.logger("srm_core").info(summary)
	print(summary)
