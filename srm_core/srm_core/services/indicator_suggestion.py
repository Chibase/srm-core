# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

"""
Rule-based indicator suggestion engine for Communication Objectives.

Phase 1: Simple rule-based suggestions based on objective type.
Future phases: OpenAI integration for more sophisticated suggestions.
"""


INDICATOR_SUGGESTIONS = {
	"Awareness": [
		"% of target audience aware of key message",
		"% of target audience recalled campaign/initiative",
		"Number of impressions or reach metric",
		"% of stakeholders who have heard about initiative",
	],
	"Understanding": [
		"% understanding key concepts or process",
		"% able to explain initiative correctly",
		"% who can identify eligibility criteria",
		"% demonstrating knowledge of intended changes",
	],
	"Trust": [
		"Trust score or rating (scale)",
		"% who trust organization or initiative",
		"Net Promoter Score (NPS) for initiative",
		"% confidence in outcomes",
	],
	"Participation": [
		"% participation rate in activity/program",
		"Number of participants engaged",
		"% attendance at events or sessions",
		"Engagement rate (posts, comments, shares)",
	],
	"Behaviour Change": [
		"% demonstrating new behavior",
		"% who adopted recommended practice",
		"Frequency of behavior change (times per month)",
		"% sustained behavior change after intervention",
	],
	"Service Uptake": [
		"% service uptake rate",
		"Number of people accessing service",
		"% increase in service utilization",
		"Average time from awareness to uptake (days)",
	],
}


def get_suggested_indicators(objective_type):
	"""
	Return a list of suggested indicator names based on objective type.
	
	Args:
		objective_type (str): One of 'Awareness', 'Understanding', 'Trust',
		                      'Participation', 'Behaviour Change', 'Service Uptake'
	
	Returns:
		list: Suggested indicator text strings
	"""
	return INDICATOR_SUGGESTIONS.get(objective_type, [])
