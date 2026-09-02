# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Outcome Measurement Service for Phase 2.

Measures outcomes by type:
- Awareness: % aware of initiative
- Understanding: % who understand concepts
- Trust: Trust score/rating
- Participation: % participation or count
- Behaviour Change: % demonstrating new behavior
- Service Uptake: % utilizing service

Phase 2: Measurement only. No AI analysis, attribution, or causal inference.
"""

import frappe
from frappe import logger
from datetime import datetime
from typing import Dict, List, Optional, Tuple


OUTCOME_TYPES = {
    "Awareness": {
        "description": "% of target audience aware of key message",
        "unit": "%",
        "measurement_method": "Survey, monitoring data",
    },
    "Understanding": {
        "description": "% understanding key concepts or process",
        "unit": "%",
        "measurement_method": "Knowledge assessment, survey",
    },
    "Trust": {
        "description": "Trust score or rating (scale)",
        "unit": "Score (1-10) or %",
        "measurement_method": "Trust survey, NPS",
    },
    "Participation": {
        "description": "% participation rate or count engaged",
        "unit": "% or count",
        "measurement_method": "Event attendance, engagement logs",
    },
    "Behaviour Change": {
        "description": "% demonstrating new behavior",
        "unit": "%",
        "measurement_method": "Behavioral observation, self-report",
    },
    "Service Uptake": {
        "description": "% service uptake rate",
        "unit": "%",
        "measurement_method": "Service enrollment, usage logs",
    },
}


def get_outcome_type_info(outcome_type: str) -> Dict:
    """
    Get metadata for an outcome type.
    
    Args:
        outcome_type (str): One of the defined outcome types
    
    Returns:
        dict: Outcome type metadata
    """
    return OUTCOME_TYPES.get(outcome_type, {})


def validate_outcome_type(outcome_type: str) -> bool:
    """
    Check if outcome type is valid.
    
    Args:
        outcome_type (str): Outcome type to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    return outcome_type in OUTCOME_TYPES


def get_all_outcome_types() -> List[str]:
    """
    Get list of all valid outcome types.
    
    Returns:
        list: Outcome type names
    """
    return list(OUTCOME_TYPES.keys())


def measure_outcome(
    objective_name: str,
    outcome_type: str,
    measurement_value: float,
    measurement_date: str,
    notes: str = None
) -> Dict:
    """
    Record a measurement for an outcome.
    
    Args:
        objective_name (str): Communication Objective name
        outcome_type (str): Type of outcome (Awareness, Understanding, etc)
        measurement_value (float): Measured value
        measurement_date (str): Date of measurement (YYYY-MM-DD)
        notes (str): Optional notes
    
    Returns:
        dict: Created Measurement Record data
    
    Raises:
        frappe.ValidationError: If objective not found or invalid outcome type
    """
    if not validate_outcome_type(outcome_type):
        frappe.throw(f"Invalid outcome type: {outcome_type}")
    
    # Fetch objective to get linked indicator
    objective = frappe.get_doc("Communication Objective", objective_name)
    
    if not objective.impact_indicator:
        frappe.throw(
            f"Communication Objective {objective_name} has no linked Impact Indicator. "
            "Cannot record measurement without indicator."
        )
    
    # Create measurement record
    measurement = frappe.get_doc({
        "doctype": "Measurement Record",
        "impact_indicator": objective.impact_indicator,
        "measurement_date": measurement_date,
        "measured_value": measurement_value,
        "notes": notes or f"Outcome type: {outcome_type}",
        "measured_by": frappe.session.user,
    })
    
    measurement.insert(ignore_permissions=True)
    logger().info(f"Recorded {outcome_type} measurement: {measurement_value} on {measurement_date}")
    
    return {
        "measurement_name": measurement.name,
        "value": measurement_value,
        "date": measurement_date,
        "outcome_type": outcome_type,
    }


def get_outcome_measurements(
    objective_name: str,
    outcome_type: str = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fetch all measurements for an objective, optionally filtered by outcome type.
    
    Args:
        objective_name (str): Communication Objective name
        outcome_type (str, optional): Filter by outcome type
        limit (int): Maximum number of records to return
    
    Returns:
        list: Measurement records sorted by date (ascending)
    """
    objective = frappe.get_doc("Communication Objective", objective_name)
    
    if not objective.impact_indicator:
        return []
    
    measurements = frappe.db.get_list(
        "Measurement Record",
        filters={"impact_indicator": objective.impact_indicator},
        fields=[
            "name",
            "measurement_date",
            "measured_value",
            "notes",
            "measured_by",
            "verified_by"
        ],
        order_by="measurement_date asc",
        limit_page_length=limit
    )
    
    # Convert to dicts with outcome_type extracted from notes if applicable
    result = []
    for m in measurements:
        record = {
            "name": m.name,
            "date": m.measurement_date,
            "value": m.measured_value,
            "notes": m.notes,
            "measured_by": m.measured_by,
            "verified_by": m.verified_by,
            "outcome_type": outcome_type,  # Use provided type or extract from notes
        }
        result.append(record)
    
    return result


def get_baseline_current_target(
    objective_name: str
) -> Tuple[Optional[float], Optional[float], float]:
    """
    Get baseline, current (latest measurement), and target for an objective.
    
    Args:
        objective_name (str): Communication Objective name
    
    Returns:
        tuple: (baseline, current, target)
    """
    objective = frappe.get_doc("Communication Objective", objective_name)
    
    baseline = objective.baseline_value
    target = objective.target_value
    
    # Get latest measurement
    latest = frappe.db.get_list(
        "Measurement Record",
        filters={"impact_indicator": objective.impact_indicator},
        fields=["measured_value"],
        order_by="measurement_date desc",
        limit_page_length=1
    )
    
    current = latest[0].measured_value if latest else baseline
    
    return baseline, current, target
