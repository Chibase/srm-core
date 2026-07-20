"""Impact assessment helpers and scoring for SRM Core."""

import frappe
from frappe import _
from frappe.utils import cint, flt

OBSERVED_SEVERITY_ORDINALS = {
	"Very Low": 1,
	"Low": 2,
	"Medium": 3,
	"High": 4,
	"Very High": 5,
}

VALID_OBSERVED_SEVERITIES = frozenset(OBSERVED_SEVERITY_ORDINALS.keys())

MAX_SEVERITY_ORDINAL = 5


def severity_to_ordinal(severity):
	"""Map severity label to ordinal; returns None for unknown labels."""
	if severity is None:
		return None
	return OBSERVED_SEVERITY_ORDINALS.get(severity)


def get_taxonomy_weight(taxonomy_name, weight_by_taxonomy=None):
	weight = None
	if weight_by_taxonomy is not None:
		weight = weight_by_taxonomy.get(taxonomy_name)
	else:
		weight = frappe.db.get_value("SRM Impact Taxonomy", taxonomy_name, "default_weight")

	weight = flt(weight)
	if weight <= 0:
		return 1.0
	return weight


def compute_weighted_score(rows, weight_by_taxonomy=None):
	"""Compute normalized impact score (0-100) from assessment rows."""
	if not rows:
		return 0.0

	weighted_sum = 0.0
	weight_sum = 0.0

	for row in rows:
		severity = severity_to_ordinal(row.observed_severity)
		if severity is None:
			continue

		weight = get_taxonomy_weight(row.impact_taxonomy, weight_by_taxonomy)
		weighted_sum += severity * weight
		weight_sum += weight

	if weight_sum <= 0:
		return 0.0

	normalized = (weighted_sum / (weight_sum * MAX_SEVERITY_ORDINAL)) * 100
	return round(normalized, 2)


def score_to_band(score):
	"""Map normalized score to impact band label."""
	value = flt(score)
	if value < 25:
		return "Low"
	if value < 50:
		return "Moderate"
	if value < 75:
		return "High"
	return "Critical"


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

		if row.observed_severity not in VALID_OBSERVED_SEVERITIES:
			frappe.throw(
				_("Invalid observed severity: {0}. Allowed values are {1}.").format(
					row.observed_severity,
					", ".join(sorted(VALID_OBSERVED_SEVERITIES)),
				)
			)

		if not cint(frappe.db.get_value("SRM Impact Taxonomy", row.impact_taxonomy, "is_active")):
			frappe.throw(_("Impact taxonomy {0} is inactive and cannot be used.").format(row.impact_taxonomy))

	duplicates = find_duplicate_taxonomies(rows)
	if duplicates:
		frappe.throw(
			_("Duplicate impact taxonomy rows are not allowed: {0}").format(", ".join(sorted(duplicates)))
		)
