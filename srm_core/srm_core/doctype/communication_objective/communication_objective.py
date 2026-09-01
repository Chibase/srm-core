# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from srm_core.services.indicator_suggestion import get_suggested_indicators


class CommunicationObjective(Document):
	"""Define the intended change associated with a communication intervention.
	
	Links to an Impact Indicator for measurement and Progress tracking.
	"""

	def on_load(self):
		"""When form loads, populate AI-suggested indicators if objective_type is set."""
		if self.objective_type and not self.suggested_indicators:
			suggestions = get_suggested_indicators(self.objective_type)
			for suggestion in suggestions:
				self.append('suggested_indicators', {
					'suggestion_text': suggestion
				})

	def validate(self):
		"""Validate objective coherence."""
		if self.baseline_value is not None and self.target_value is not None:
			if self.baseline_value == self.target_value:
				frappe.throw(
					"Target Value must differ from Baseline Value. "
					"Progress calculation will fail if they are equal."
				)

	def on_update(self):
		"""When objective is updated, trigger related snapshot calculation if indicator is linked."""
		if self.impact_indicator:
			# Could trigger async snapshot generation here in a future phase
			pass
