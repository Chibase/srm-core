import frappe
from frappe.utils import add_to_date, flt, get_datetime, now_datetime

from srm_core.services.priority import (
	compute_priority_score,
	priority_band,
	resolve_sentiment_signal,
	sla_hours_for_priority,
)


def execute():
	updated = 0
	now = now_datetime()

	for row in frappe.get_all(
		"SRM Incident",
		fields=["name", "creation", "geographic_area", "impact_score", "status", "priority_level"],
	):
		if row.priority_level:
			continue

		impact_score = flt(row.impact_score)
		sentiment = resolve_sentiment_signal(
			row.name,
			row.geographic_area,
			reference_datetime=row.creation or now,
		)
		priority_score = compute_priority_score(impact_score, sentiment)
		priority_level = priority_band(priority_score)
		sla_hours = sla_hours_for_priority(priority_level)
		base = get_datetime(row.creation or now)
		sla_due_by = add_to_date(base, hours=sla_hours)

		frappe.db.set_value(
			"SRM Incident",
			row.name,
			{
				"priority_score": priority_score,
				"priority_level": priority_level,
				"priority_computed_on": now,
				"priority_computed_by": "Administrator",
				"sla_target_hours": sla_hours,
				"sla_due_by": sla_due_by,
				"sla_due_date": sla_due_by,
			},
			update_modified=False,
		)
		updated += 1

	frappe.db.commit()
	summary = f"Incident priority/SLA backfill: updated={updated}"
	frappe.logger("srm_core").info(summary)
	print(summary)
