import frappe

DEFAULT_IMPACT_TAXONOMIES = (
	{
		"taxonomy_name": "Community Trust",
		"impact_category": "Social",
		"default_weight": 1.0,
		"sort_order": 1,
	},
	{
		"taxonomy_name": "Regulatory Exposure",
		"impact_category": "Regulatory",
		"default_weight": 1.0,
		"sort_order": 2,
	},
	{
		"taxonomy_name": "Service Continuity",
		"impact_category": "Operational",
		"default_weight": 1.0,
		"sort_order": 3,
	},
	{
		"taxonomy_name": "Financial Exposure",
		"impact_category": "Financial",
		"default_weight": 1.0,
		"sort_order": 4,
	},
)


def ensure_srm_lead_role():
	if frappe.db.exists("Role", "SRM Lead"):
		return

	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": "SRM Lead",
			"desk_access": 1,
		}
	).insert(ignore_permissions=True)


def execute():
	ensure_srm_lead_role()

	created = 0
	for row in DEFAULT_IMPACT_TAXONOMIES:
		if frappe.db.exists("SRM Impact Taxonomy", row["taxonomy_name"]):
			continue

		frappe.get_doc(
			{
				"doctype": "SRM Impact Taxonomy",
				"is_active": 1,
				**row,
			}
		).insert(ignore_permissions=True)
		created += 1

	frappe.db.commit()
	summary = f"Impact taxonomy seed: created={created}"
	frappe.logger("srm_core").info(summary)
	print(summary)
