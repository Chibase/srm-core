# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

import unittest
from srm_core.services.indicator_suggestion import get_suggested_indicators


class TestIndicatorSuggestion(unittest.TestCase):
	"""Test suite for AI indicator suggestion engine."""

	def test_suggest_awareness_indicators(self):
		"""Test indicator suggestions for Awareness objective."""
		suggestions = get_suggested_indicators("Awareness")
		self.assertIsInstance(suggestions, list)
		self.assertGreater(len(suggestions), 0)
		self.assertTrue(any("aware" in s.lower() for s in suggestions))

	def test_suggest_understanding_indicators(self):
		"""Test indicator suggestions for Understanding objective."""
		suggestions = get_suggested_indicators("Understanding")
		self.assertIsInstance(suggestions, list)
		self.assertGreater(len(suggestions), 0)
		self.assertTrue(any("understand" in s.lower() for s in suggestions))

	def test_suggest_trust_indicators(self):
		"""Test indicator suggestions for Trust objective."""
		suggestions = get_suggested_indicators("Trust")
		self.assertIsInstance(suggestions, list)
		self.assertGreater(len(suggestions), 0)
		self.assertTrue(any("trust" in s.lower() for s in suggestions))

	def test_suggest_participation_indicators(self):
		"""Test indicator suggestions for Participation objective."""
		suggestions = get_suggested_indicators("Participation")
		self.assertIsInstance(suggestions, list)
		self.assertGreater(len(suggestions), 0)
		self.assertTrue(any("particip" in s.lower() for s in suggestions))

	def test_suggest_behaviour_change_indicators(self):
		"""Test indicator suggestions for Behaviour Change objective."""
		suggestions = get_suggested_indicators("Behaviour Change")
		self.assertIsInstance(suggestions, list)
		self.assertGreater(len(suggestions), 0)
		self.assertTrue(any("behav" in s.lower() for s in suggestions))

	def test_suggest_service_uptake_indicators(self):
		"""Test indicator suggestions for Service Uptake objective."""
		suggestions = get_suggested_indicators("Service Uptake")
		self.assertIsInstance(suggestions, list)
		self.assertGreater(len(suggestions), 0)
		self.assertTrue(any("uptake" in s.lower() for s in suggestions))

	def test_suggest_unknown_objective_type(self):
		"""Test suggestions for unknown objective type return empty list."""
		suggestions = get_suggested_indicators("Unknown Type")
		self.assertEqual(suggestions, [])



if __name__ == "__main__":
	unittest.main()
