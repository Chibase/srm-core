# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Progress Calculation Engine for Impact Framework.

Handles:
- Progress % calculation: ((Current - Baseline) / (Target - Baseline)) × 100
- Progress status inference: On Track / Needs Attention / Completed / Not Started
- Division-by-zero protection
- Invalid/missing value handling
"""

import frappe
from frappe import logger
from datetime import datetime


PROGRESS_THRESHOLD = 0.8  # 80% - On Track if progress >= threshold


def calculate_progress(
	baseline_value,
	current_value,
	target_value,
	strict=True
):
	"""
	Calculate progress toward target as a percentage.
	
	Formula: ((Current - Baseline) / (Target - Baseline)) × 100
	
	Args:
		baseline_value (float): Starting value
		current_value (float): Current measured value
		target_value (float): Desired end value
		strict (bool): If True, raise error on division by zero.
		               If False, return None.
	
	Returns:
		float or None: Progress percentage (0-100+), or None if invalid
	
	Raises:
		frappe.ValidationError: If strict=True and Target == Baseline
	"""
	# Guard against None values
	if baseline_value is None or current_value is None or target_value is None:
		if strict:
			frappe.throw("Cannot calculate progress with missing values (baseline, current, or target).")
		return None

	# Guard against division by zero
	divisor = target_value - baseline_value
	if divisor == 0:
		if strict:
			frappe.throw(
				"Cannot calculate progress: Target Value equals Baseline Value. "
				"Progress calculation requires Target ≠ Baseline."
			)
		logger().warning(
			f"Progress calculation skipped: baseline={baseline_value}, target={target_value} (equal values)"
		)
		return None

	# Calculate progress
	numerator = current_value - baseline_value
	progress_pct = (numerator / divisor) * 100

	return progress_pct


def infer_progress_status(
	progress_percentage,
	current_value,
	target_value,
	baseline_value,
	threshold=PROGRESS_THRESHOLD
):
	"""
	Infer progress status from calculated progress percentage.
	
	Rules:
	- Completed: current == target (within tolerance)
	- Not Started: current == baseline (within tolerance)
	- On Track: progress >= threshold (e.g., 80%)
	- Needs Attention: 0 < progress < threshold
	
	Args:
		progress_percentage (float): Calculated progress %
		current_value (float): Current measured value
		target_value (float): Target value
		baseline_value (float): Baseline value
		threshold (float): Threshold ratio for 'On Track' (default 0.8 = 80%)
	
	Returns:
		str: Status ('On Track', 'Needs Attention', 'Completed', 'Not Started')
	"""
	if progress_percentage is None:
		return "Not Started"

	TOLERANCE = 0.01  # 1% tolerance for equality checks

	# Check if completed (current ≈ target)
	if abs(current_value - target_value) / abs(target_value) < TOLERANCE if target_value != 0 else False:
		return "Completed"

	# Check if not started (current ≈ baseline)
	if abs(current_value - baseline_value) / abs(baseline_value) < TOLERANCE if baseline_value != 0 else False:
		return "Not Started"

	# Normalize progress_percentage to 0-1 range for comparison
	normalized_progress = progress_percentage / 100.0

	# Check if on track
	if normalized_progress >= threshold:
		return "On Track"

	# Otherwise needs attention
	return "Needs Attention"


def create_impact_snapshot(indicator_doc, current_value=None):
	"""
	Create or update an Impact Snapshot for an indicator.
	
	Uses the most recent Measurement Record to populate current_value.
	Calculates progress and infers status.
	
	Args:
		indicator_doc (Document): Impact Indicator document
		current_value (float, optional): Override current value. If None, fetches latest measurement.
	
	Returns:
		Document: Created/updated Impact Snapshot
	"""
	if not indicator_doc.name:
		frappe.throw("Impact Indicator must be saved before creating snapshots.")

	# Fetch latest measurement if not provided
	if current_value is None:
		latest_measurement = frappe.db.get_list(
			"Measurement Record",
			filters={"impact_indicator": indicator_doc.name},
			order_by="measurement_date desc",
			limit_page_length=1,
			fields=["measured_value"]
		)
		if latest_measurement:
			current_value = latest_measurement[0].get("measured_value")
		else:
			# No measurements yet; use baseline as current
			current_value = indicator_doc.baseline_value

	# Calculate progress
	progress_pct = calculate_progress(
		indicator_doc.baseline_value,
		current_value,
		indicator_doc.target_value,
		strict=False
	)

	# Infer status
	status = infer_progress_status(
		progress_pct,
		current_value,
		indicator_doc.target_value,
		indicator_doc.baseline_value
	)

	# Create snapshot
	snapshot = frappe.get_doc({
		"doctype": "Impact Snapshot",
		"impact_indicator": indicator_doc.name,
		"snapshot_date": frappe.utils.today(),
		"baseline_value": indicator_doc.baseline_value,
		"current_value": current_value,
		"target_value": indicator_doc.target_value,
		"progress_percentage": progress_pct,
		"progress_status": status,
		"calculated_at": datetime.now(),
	})

	snapshot._allow_save = True  # Override read-only protection
	snapshot.insert(ignore_permissions=True)

	return snapshot
