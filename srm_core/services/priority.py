"""Priority scoring and SLA targeting helpers for SRM Core."""

import frappe
from frappe.utils import add_to_date, flt, get_datetime, now_datetime

IMPACT_WEIGHT = 0.70
SENTIMENT_MAX_CONTRIBUTION = 30.0
SENTIMENT_INTENSITY_MIN = -100.0
SENTIMENT_INTENSITY_MAX = 100.0
SENTIMENT_LOOKBACK_DAYS = 30

PRIORITY_P4_LOW = "P4-Low"
PRIORITY_P3_MEDIUM = "P3-Medium"
PRIORITY_P2_HIGH = "P2-High"
PRIORITY_P1_CRITICAL = "P1-Critical"

PRIORITY_SLA_HOURS = {
	PRIORITY_P1_CRITICAL: 4.0,
	PRIORITY_P2_HIGH: 12.0,
	PRIORITY_P3_MEDIUM: 24.0,
	PRIORITY_P4_LOW: 72.0,
}


def normalize_sentiment_intensity(sentiment_score):
	"""Map raw sentiment score (-100..100) to a 0-30 priority contribution."""
	value = flt(sentiment_score)
	if value < SENTIMENT_INTENSITY_MIN:
		value = SENTIMENT_INTENSITY_MIN
	elif value > SENTIMENT_INTENSITY_MAX:
		value = SENTIMENT_INTENSITY_MAX

	intensity = abs(value)
	contribution = (intensity / abs(SENTIMENT_INTENSITY_MAX)) * SENTIMENT_MAX_CONTRIBUTION
	return round(contribution, 2)


def compute_priority_score(impact_score, sentiment_signal):
	"""Combine impact (0-70) and sentiment intensity (0-30) into priority score capped at 100."""
	impact_contrib = round(flt(impact_score) * IMPACT_WEIGHT, 2)
	if impact_contrib < 0:
		impact_contrib = 0.0
	elif impact_contrib > 70.0:
		impact_contrib = 70.0

	sentiment_contrib = normalize_sentiment_intensity(sentiment_signal)
	total = round(impact_contrib + sentiment_contrib, 2)
	if total < 0:
		return 0.0
	if total > 100.0:
		return 100.0
	return total


def priority_band(score):
	"""Map priority score to P1-P4 level using quartile thresholds."""
	value = flt(score)
	if value < 25:
		return PRIORITY_P4_LOW
	if value < 50:
		return PRIORITY_P3_MEDIUM
	if value < 75:
		return PRIORITY_P2_HIGH
	return PRIORITY_P1_CRITICAL


def sla_hours_for_priority(level):
	"""Return SLA target hours for a priority level; defaults to P4 when unknown."""
	return PRIORITY_SLA_HOURS.get(level, PRIORITY_SLA_HOURS[PRIORITY_P4_LOW])


def resolve_sentiment_signal(incident_name, geographic_area, reference_datetime=None):
	"""Resolve latest sentiment intensity for an incident context.

	Prefer rows linked directly via SRM Sentiment Capture.linked_incident.
	Fallback: same geographic_area within SENTIMENT_LOOKBACK_DAYS of reference time.
	Returns raw sentiment_score or 0.0 when no signal is found.
	"""
	if incident_name:
		linked = frappe.get_all(
			"SRM Sentiment Capture",
			filters={"linked_incident": incident_name},
			fields=["sentiment_score", "capture_date", "creation"],
			order_by="capture_date desc, creation desc",
			limit=1,
		)
		if linked:
			return flt(linked[0].sentiment_score)

	if not geographic_area:
		return 0.0

	reference = get_datetime(reference_datetime or now_datetime())
	window_start = add_to_date(reference, days=-SENTIMENT_LOOKBACK_DAYS)

	fallback = frappe.get_all(
		"SRM Sentiment Capture",
		filters={
			"geographic_area": geographic_area,
			"capture_date": [">=", window_start.date()],
		},
		fields=["sentiment_score", "capture_date", "creation"],
		order_by="capture_date desc, creation desc",
		limit=1,
	)
	if fallback:
		return flt(fallback[0].sentiment_score)

	return 0.0
