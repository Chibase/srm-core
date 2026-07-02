import frappe

from srm_core.services.geographic_area import get_or_create_geographic_area


def execute():
	created = 0
	linked_incidents = 0
	linked_sentiments = 0

	for row in frappe.get_all(
		"SRM Incident",
		fields=["name", "geographic_area_text", "geographic_area"],
		filters={"geographic_area": ["is", "not set"]},
	):
		area_name = (row.geographic_area_text or "").strip()
		if not area_name:
			continue

		area, was_created = get_or_create_geographic_area(area_name)
		if was_created:
			created += 1

		frappe.db.set_value(
			"SRM Incident",
			row.name,
			"geographic_area",
			area,
			update_modified=False,
		)
		linked_incidents += 1

	for row in frappe.get_all(
		"SRM Sentiment Capture",
		fields=["name", "geographic_area_text", "geographic_area"],
		filters={"geographic_area": ["is", "not set"]},
	):
		area_name = (row.geographic_area_text or "").strip()
		if not area_name:
			continue

		area, was_created = get_or_create_geographic_area(area_name)
		if was_created:
			created += 1

		frappe.db.set_value(
			"SRM Sentiment Capture",
			row.name,
			"geographic_area",
			area,
			update_modified=False,
		)
		linked_sentiments += 1

	frappe.db.commit()

	summary = (
		f"Geographic Area migration: created={created}, "
		f"linked_incidents={linked_incidents}, linked_sentiments={linked_sentiments}"
	)
	frappe.logger("srm_core").info(summary)
	print(summary)
