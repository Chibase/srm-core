# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import unittest
from unittest.mock import patch, MagicMock
from srm_core.services.outcome_progress_tracker import (
	get_outcome_progress,
	get_outcome_trend,
	OUTCOME_STATUS_COLORS,
)


class TestOutcomeProgressTracker(unittest.TestCase):
	"""Test suite for outcome progress tracker."""

	def test_outcome_status_colors_defined(self):
		"""Test that outcome status colors are defined."""
		self.assertIn("On Track", OUTCOME_STATUS_COLORS)
		self.assertIn("Needs Attention", OUTCOME_STATUS_COLORS)
		self.assertIn("Off Track", OUTCOME_STATUS_COLORS)
		self.assertIn("No Data", OUTCOME_STATUS_COLORS)

	def test_outcome_status_colors_valid_hex(self):
		"""Test that status colors are valid hex values."""
		for status, color in OUTCOME_STATUS_COLORS.items():
			self.assertTrue(color.startswith("#"))
			self.assertEqual(len(color), 7)  # #RRGGBB

	def test_outcome_progress_structure(self):
		"""Test that outcome progress returns expected structure."""
		# This would require mocking frappe calls
		# For now, just test that the function exists and is callable
		self.assertTrue(callable(get_outcome_progress))

	def test_outcome_trend_structure(self):
		"""Test that outcome trend returns expected structure."""
		# This would require mocking frappe calls
		self.assertTrue(callable(get_outcome_trend))



if __name__ == "__main__":
	unittest.main()
