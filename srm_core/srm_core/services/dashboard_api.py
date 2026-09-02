# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Dashboard Data API for Phase 2.

Exposes outcome measurement and progress data via Frappe API.

Endpoints:
- /api/method/srm_core.services.dashboard_api.get_intervention_dashboard
- /api/method/srm_core.services.dashboard_api.get_outcome_trend
- /api/method/srm_core.services.dashboard_api.get_all_interventions_summary
"""

import frappe
from frappe.decorators import whitelist
from srm_core.services.outcome_progress_tracker import (
    get_outcome_progress,
    get_outcome_trend,
    get_intervention_outcome_summary,
    get_dashboard_data,
)


@whitelist(allow_guest=False)
def get_intervention_dashboard(intervention_name: str) -> dict:
    """
    Get complete dashboard data for an intervention.
    
    Endpoint: /api/method/srm_core.services.dashboard_api.get_intervention_dashboard
    Query params: intervention_name=[name]
    
    Returns:
        dict with outcome summary for all objectives
    """
    if not intervention_name:
        frappe.throw("intervention_name is required")
    
    # Verify intervention exists and user can view it
    if not frappe.db.exists("Communication Intervention", intervention_name):
        frappe.throw(f"Communication Intervention {intervention_name} not found")
    
    return get_intervention_outcome_summary(intervention_name)


@whitelist(allow_guest=False)
def get_outcome_trend_api(objective_name: str) -> dict:
    """
    Get trend data for an objective's measurements.
    
    Endpoint: /api/method/srm_core.services.dashboard_api.get_outcome_trend_api
    Query params: objective_name=[name]
    
    Returns:
        dict with trend data (baseline, measurements, target)
    """
    if not objective_name:
        frappe.throw("objective_name is required")
    
    if not frappe.db.exists("Communication Objective", objective_name):
        frappe.throw(f"Communication Objective {objective_name} not found")
    
    return get_outcome_trend(objective_name)


@whitelist(allow_guest=False)
def get_objective_progress(objective_name: str) -> dict:
    """
    Get current progress for a single objective.
    
    Endpoint: /api/method/srm_core.services.dashboard_api.get_objective_progress
    Query params: objective_name=[name]
    
    Returns:
        dict with progress data
    """
    if not objective_name:
        frappe.throw("objective_name is required")
    
    if not frappe.db.exists("Communication Objective", objective_name):
        frappe.throw(f"Communication Objective {objective_name} not found")
    
    return get_outcome_progress(objective_name)


@whitelist(allow_guest=False)
def get_all_interventions_summary() -> dict:
    """
    Get aggregated summary for all interventions.
    
    Endpoint: /api/method/srm_core.services.dashboard_api.get_all_interventions_summary
    
    Returns:
        dict with all interventions and overall metrics
    """
    return get_dashboard_data()
