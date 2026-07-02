"""Impact assessment helpers for SRM Core (scoring deferred to Packet 06)."""

import frappe
from frappe import _
from frappe.utils import cint

OBSERVED_SEVERITY_ORDINALS = {
	"Very Low": 1,
	"Low": 2,
	"Medium": 3,
	"High": 4,
	"Very High": 5,
}


def severity_to_ordinal(severity):
	"""Map severity label to ordinal placeholder for future scoring."""
	return OBSERVED_SEVERITY_ORDINALS.get(severity)


def find_duplicate_taxonomies(rows, taxonomy_field="impact_taxonomy"):
	seen = set()
	duplicates = set()

	for row in rows:
		taxonomy = row.get(taxonomy_field) if isinstance(row, dict) else getattr(row, taxonomy_field, None)
		if not taxonomy:
			continue
		if taxonomy in seen:
			duplicates.add(taxonomy)
		seen.add(taxonomy)

	return duplicates


def validate_impact_assessment_rows(rows):
	if not rows:
		return

	for row in rows:
		if not row.impact_taxonomy:
			frappe.throw(_("Impact Taxonomy is required for each impact assessment row."))

		if not row.observed_severity:
			frappe.throw(_("Observed Severity is required for each impact assessment row."))

		if not cint(frappe.db.get_value("SRM Impact Taxonomy", row.impact_taxonomy, "is_active")):
			frappe.throw(
				_("Impact taxonomy {0} is inactive and cannot be used.").format(row.impact_taxonomy)
			)

	duplicates = find_duplicate_taxonomies(rows)
	if duplicates:
		frappe.throw(
			_("Duplicate impact taxonomy rows are not allowed: {0}").format(", ".join(sorted(duplicates)))
		)
