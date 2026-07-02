import frappe

from srm_core.services.risk_rollup import apply_incident_risk_linkage


def execute():
	updated = 0
	for row in frappe.get_all(
		"SRM Incident",
		filters={"linked_risk": ["is", "set"]},
		fields=["name"],
	):
		doc = frappe.get_doc("SRM Incident", row.name)
		previous_score = doc.residual_risk_score
		previous_band = doc.residual_risk_band
		apply_incident_risk_linkage(doc, previous=doc)
		if (
			doc.residual_risk_score != previous_score
			or doc.residual_risk_band != previous_band
			or not previous_band
		):
			updated += 1

	frappe.db.commit()
	summary = f"Incident residual risk backfill: updated={updated}"
	frappe.logger("srm_core").info(summary)
	print(summary)
