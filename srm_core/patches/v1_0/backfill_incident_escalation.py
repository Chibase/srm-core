import frappe
from frappe.utils import cint, flt, now_datetime

from srm_core.services.escalation import (
	ESCALATION_NONE,
	build_auto_escalation_reason,
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
		reason = (
			build_auto_escalation_reason(
				level,
				row.priority_level or "",
				is_sla_breached,
				row.impact_band or "",
				requires_exec=requires_exec,
			)
			if is_escalated
			else None
		)

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
