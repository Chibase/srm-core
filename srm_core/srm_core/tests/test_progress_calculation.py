# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import unittest
from unittest.mock import patch, MagicMock
from srm_core.services.progress_calculation import (
	calculate_progress,
	infer_progress_status,
	PROGRESS_THRESHOLD,
)


class TestProgressCalculation(unittest.TestCase):
	"""Test suite for progress calculation engine."""

	def test_calculate_progress_normal_case(self):
		"""Test normal progress calculation."""
		# Scenario: Baseline 32%, Current 68%, Target 75%
		progress = calculate_progress(
			baseline_value=32,
			current_value=68,
			target_value=75,
			strict=False
		)
		# Expected: (68-32)/(75-32) * 100 = 36/43 * 100 = 83.72%
		self.assertAlmostEqual(progress, 83.72, places=1)

	def test_calculate_progress_at_baseline(self):
		"""Test progress when current equals baseline."""
		progress = calculate_progress(
			baseline_value=32,
			current_value=32,
			target_value=75,
			strict=False
		)
		# Expected: 0%
		self.assertEqual(progress, 0.0)

	def test_calculate_progress_at_target(self):
		"""Test progress when current equals target."""
		progress = calculate_progress(
			baseline_value=32,
			current_value=75,
			target_value=75,
			strict=False
		)
		# Expected: 100%
		self.assertEqual(progress, 100.0)

	def test_calculate_progress_beyond_target(self):
		"""Test progress when current exceeds target."""
		progress = calculate_progress(
			baseline_value=32,
			current_value=85,
			target_value=75,
			strict=False
		)
		# Expected: (85-32)/(75-32) * 100 = 53/43 * 100 = 123.26%
		self.assertAlmostEqual(progress, 123.26, places=1)

	def test_calculate_progress_division_by_zero_strict(self):
		"""Test that division by zero raises error in strict mode."""
		with self.assertRaises(Exception):
			calculate_progress(
				baseline_value=50,
				current_value=50,
				target_value=50,  # Equal to baseline
				strict=True
			)

	def test_calculate_progress_division_by_zero_non_strict(self):
		"""Test that division by zero returns None in non-strict mode."""
		progress = calculate_progress(
			baseline_value=50,
			current_value=50,
			target_value=50,  # Equal to baseline
			strict=False
		)
		self.assertIsNone(progress)

	def test_calculate_progress_missing_values(self):
		"""Test that missing values are handled."""
		progress = calculate_progress(
			baseline_value=None,
			current_value=50,
			target_value=75,
			strict=False
		)
		self.assertIsNone(progress)

	def test_infer_progress_status_completed(self):
		"""Test status inference when target is reached."""
		status = infer_progress_status(
			progress_percentage=100,
			current_value=75,
			target_value=75,
			baseline_value=32
		)
		self.assertEqual(status, "Completed")

	def test_infer_progress_status_not_started(self):
		"""Test status inference when no progress."""
		status = infer_progress_status(
			progress_percentage=0,
			current_value=32,
			target_value=75,
			baseline_value=32
		)
		self.assertEqual(status, "Not Started")

	def test_infer_progress_status_on_track(self):
		"""Test status inference when progress is on track (>= threshold)."""
		status = infer_progress_status(
			progress_percentage=83.72,  # Above 80% threshold
			current_value=68,
			target_value=75,
			baseline_value=32
		)
		self.assertEqual(status, "On Track")

	def test_infer_progress_status_needs_attention(self):
		"""Test status inference when progress is below threshold."""
		status = infer_progress_status(
			progress_percentage=50,  # Below 80% threshold
			current_value=55,
			target_value=75,
			baseline_value=32
		)
		self.assertEqual(status, "Needs Attention")

	def test_infer_progress_status_none_progress(self):
		"""Test status inference with None progress."""
		status = infer_progress_status(
			progress_percentage=None,
			current_value=32,
			target_value=75,
			baseline_value=32
		)
		self.assertEqual(status, "Not Started")



if __name__ == "__main__":
	unittest.main()
