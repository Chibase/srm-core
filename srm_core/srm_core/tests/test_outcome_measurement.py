# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import unittest
from unittest.mock import patch, MagicMock
from srm_core.services.outcome_measurement import (
	get_outcome_type_info,
	validate_outcome_type,
	get_all_outcome_types,
	get_baseline_current_target,
)


class TestOutcomeMeasurement(unittest.TestCase):
	"""Test suite for outcome measurement engine."""

	def test_get_outcome_type_info_awareness(self):
		"""Test getting info for Awareness outcome type."""
		info = get_outcome_type_info("Awareness")
		self.assertEqual(info["unit"], "%")
		self.assertIn("aware", info["description"].lower())

	def test_get_outcome_type_info_understanding(self):
		"""Test getting info for Understanding outcome type."""
		info = get_outcome_type_info("Understanding")
		self.assertEqual(info["unit"], "%")
		self.assertIn("understand", info["description"].lower())

	def test_get_outcome_type_info_trust(self):
		"""Test getting info for Trust outcome type."""
		info = get_outcome_type_info("Trust")
		self.assertIn("trust", info["description"].lower())

	def test_get_outcome_type_info_participation(self):
		"""Test getting info for Participation outcome type."""
		info = get_outcome_type_info("Participation")
		self.assertIn("particip", info["description"].lower())

	def test_get_outcome_type_info_behaviour_change(self):
		"""Test getting info for Behaviour Change outcome type."""
		info = get_outcome_type_info("Behaviour Change")
		self.assertIn("behav", info["description"].lower())

	def test_get_outcome_type_info_service_uptake(self):
		"""Test getting info for Service Uptake outcome type."""
		info = get_outcome_type_info("Service Uptake")
		self.assertIn("uptake", info["description"].lower())

	def test_validate_outcome_type_valid(self):
		"""Test validation of valid outcome type."""
		self.assertTrue(validate_outcome_type("Awareness"))
		self.assertTrue(validate_outcome_type("Understanding"))
		self.assertTrue(validate_outcome_type("Trust"))

	def test_validate_outcome_type_invalid(self):
		"""Test validation of invalid outcome type."""
		self.assertFalse(validate_outcome_type("Invalid Type"))
		self.assertFalse(validate_outcome_type("Random"))

	def test_get_all_outcome_types(self):
		"""Test getting all outcome types."""
		types = get_all_outcome_types()
		self.assertEqual(len(types), 6)
		self.assertIn("Awareness", types)
		self.assertIn("Understanding", types)
		self.assertIn("Trust", types)
		self.assertIn("Participation", types)
		self.assertIn("Behaviour Change", types)
		self.assertIn("Service Uptake", types)



if __name__ == "__main__":
	unittest.main()
