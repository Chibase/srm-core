# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Outcome Progress Tracker for Phase 2.

Tracks progress toward outcome targets:
- Calculates progress % (Baseline → Current → Target)
- Infers outcome status (On Track / Needs Attention / Off Track / No Data)
- Tracks trend over time
- Aggregates multiple outcome types

Phase 2: Simple status inference only. No predictive scoring yet.
"""

import frappe
from frappe import logger
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from srm_core.services.progress_calculation import (
    calculate_progress,
    infer_progress_status,
    PROGRESS_THRESHOLD,
)


OUTCOME_STATUS_COLORS = {
    "On Track": "#10B981",  # Green
    "Needs Attention": "#F59E0B",  # Amber
    "Off Track": "#EF4444",  # Red
    "No Data": "#9CA3AF",  # Gray
}


def get_outcome_progress(
    objective_name: str
) -> Dict:
    """
    Calculate outcome progress for an objective.
    
    Returns:
        dict: {
            "objective_name": str,
            "outcome_type": str,
            "baseline": float,
            "current": float,
            "target": float,
            "progress_pct": float,
            "status": str,
            "last_measurement_date": str,
            "measurements_count": int,
        }
    """
    objective = frappe.get_doc("Communication Objective", objective_name)
    
    baseline = objective.baseline_value
    target = objective.target_value
    
    # Get latest measurement
    latest_measurement = frappe.db.get_list(
        "Measurement Record",
        filters={"impact_indicator": objective.impact_indicator},
        fields=["measured_value", "measurement_date"],
        order_by="measurement_date desc",
        limit_page_length=1
    )
    
    if not latest_measurement:
        # No data yet
        return {
            "objective_name": objective_name,
            "outcome_type": objective.objective_type,
            "baseline": baseline,
            "current": baseline,
            "target": target,
            "progress_pct": 0,
            "status": "No Data",
            "status_color": OUTCOME_STATUS_COLORS["No Data"],
            "last_measurement_date": None,
            "measurements_count": 0,
        }
    
    current = latest_measurement[0].measured_value
    last_date = latest_measurement[0].measurement_date
    
    # Calculate progress
    progress_pct = calculate_progress(
        baseline_value=baseline,
        current_value=current,
        target_value=target,
        strict=False
    )
    
    # Infer status
    if progress_pct is None:
        status = "No Data"
    elif current < baseline:
        status = "Off Track"  # Regressed
    elif progress_pct >= 100:
        status = "On Track"
    elif progress_pct >= (PROGRESS_THRESHOLD * 100):
        status = "On Track"
    else:
        status = "Needs Attention"
    
    # Count measurements
    count = frappe.db.count(
        "Measurement Record",
        filters={"impact_indicator": objective.impact_indicator}
    )
    
    return {
        "objective_name": objective_name,
        "outcome_type": objective.objective_type,
        "baseline": baseline,
        "current": current,
        "target": target,
        "progress_pct": progress_pct,
        "status": status,
        "status_color": OUTCOME_STATUS_COLORS.get(status, OUTCOME_STATUS_COLORS["No Data"]),
        "last_measurement_date": str(last_date),
        "measurements_count": count,
    }


def get_outcome_trend(
    objective_name: str,
    include_baseline_target: bool = True
) -> Dict:
    """
    Get trend of measurements over time.
    
    Args:
        objective_name (str): Communication Objective name
        include_baseline_target (bool): Include baseline and target in response
    
    Returns:
        dict: {
            "baseline": float,
            "measurements": [
                {"date": str, "value": float},
                ...
            ],
            "target": float,
        }
    """
    objective = frappe.get_doc("Communication Objective", objective_name)
    
    baseline = objective.baseline_value
    target = objective.target_value
    
    # Fetch all measurements in chronological order
    measurements = frappe.db.get_list(
        "Measurement Record",
        filters={"impact_indicator": objective.impact_indicator},
        fields=["measurement_date", "measured_value"],
        order_by="measurement_date asc"
    )
    
    trend_data = [
        {"date": str(m.measurement_date), "value": m.measured_value}
        for m in measurements
    ]
    
    result = {
        "measurements": trend_data,
    }
    
    if include_baseline_target:
        result["baseline"] = baseline
        result["target"] = target
    
    return result


def get_intervention_outcome_summary(
    intervention_name: str
) -> Dict:
    """
    Get aggregated outcome summary for all objectives of an intervention.
    
    Returns outcome progress for each outcome type represented.
    
    Returns:
        dict: {
            "intervention_name": str,
            "overall_progress_pct": float,
            "outcomes": {
                "Awareness": {progress data},
                "Understanding": {progress data},
                ...
            },
            "total_objectives": int,
            "objectives_on_track": int,
            "last_updated": str,
        }
    """
    # Fetch all objectives for this intervention
    objectives = frappe.db.get_list(
        "Communication Objective",
        filters={"intervention": intervention_name},
        fields=["name", "objective_type"],
        order_by="name asc"
    )
    
    if not objectives:
        return {
            "intervention_name": intervention_name,
            "overall_progress_pct": None,
            "outcomes": {},
            "total_objectives": 0,
            "objectives_on_track": 0,
            "last_updated": str(datetime.now()),
        }
    
    # Calculate progress for each objective, grouped by outcome type
    outcomes = {}
    progress_values = []
    on_track_count = 0
    
    for obj in objectives:
        progress_data = get_outcome_progress(obj.name)
        outcome_type = obj.objective_type
        
        if outcome_type not in outcomes:
            outcomes[outcome_type] = progress_data
        else:
            # If multiple objectives of same type, average them (simple aggregation)
            outcomes[outcome_type]["progress_pct"] = (
                outcomes[outcome_type]["progress_pct"] + progress_data["progress_pct"]
            ) / 2
        
        if progress_data["progress_pct"] is not None:
            progress_values.append(progress_data["progress_pct"])
        
        if progress_data["status"] == "On Track":
            on_track_count += 1
    
    # Calculate overall progress
    overall_progress = (
        sum(progress_values) / len(progress_values)
        if progress_values
        else None
    )
    
    return {
        "intervention_name": intervention_name,
        "overall_progress_pct": overall_progress,
        "outcomes": outcomes,
        "total_objectives": len(objectives),
        "objectives_on_track": on_track_count,
        "last_updated": str(datetime.now()),
    }


def get_dashboard_data(
    limit: int = 50
) -> Dict:
    """
    Get aggregated dashboard data for all interventions.
    
    Used for Phase 2 basic dashboard.
    
    Returns:
        dict: {
            "interventions": [
                {
                    "name": str,
                    "overall_progress": float,
                    "outcomes": {...},
                    "objectives_count": int,
                },
                ...
            ],
            "summary": {
                "total_interventions": int,
                "avg_progress": float,
            },
            "last_updated": str,
        }
    """
    # Fetch active interventions
    interventions = frappe.db.get_list(
        "Communication Intervention",
        filters={"status": ["in", ["Draft", "Active"]]},
        fields=["name"],
        limit_page_length=limit
    )
    
    intervention_data = []
    progress_values = []
    
    for intervention in interventions:
        summary = get_intervention_outcome_summary(intervention.name)
        
        if summary["overall_progress_pct"] is not None:
            progress_values.append(summary["overall_progress_pct"])
        
        intervention_data.append(summary)
    
    avg_progress = (
        sum(progress_values) / len(progress_values)
        if progress_values
        else None
    )
    
    return {
        "interventions": intervention_data,
        "summary": {
            "total_interventions": len(interventions),
            "avg_progress": avg_progress,
        },
        "last_updated": str(datetime.now()),
    }
