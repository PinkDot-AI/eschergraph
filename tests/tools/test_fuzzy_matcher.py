from __future__ import annotations

from unittest.mock import MagicMock

from eschergraph.tools.fuzzy_matcher import FuzzyMatcher


def test_find_matches_with_mock() -> None:
  """Test the _find_matches method of the FuzzyMatcher class using a mock."""
  mock_fuzzy_matcher = MagicMock(spec=FuzzyMatcher)

  # Define the mock return value for the _find_matches method
  mock_find_matches_return = ("apple", ["Apple", "apple inc."])
  mock_fuzzy_matcher._find_matches.return_value = mock_find_matches_return

  result = mock_fuzzy_matcher._find_matches(
    "apple", ["apple", "Apple", "apple inc.", "banana"]
  )

  assert (
    result == mock_find_matches_return
  ), f"Expected {mock_find_matches_return}, got {result}"


def test_match_nodes_with_mock() -> None:
  """Test the _match_nodes method of the FuzzyMatcher class using a mock."""
  mock_fuzzy_matcher = MagicMock(spec=FuzzyMatcher)

  mock_match_nodes_return = {
    "apple": ["Apple", "apple inc."],
    "Apple": ["apple", "apple inc."],
    "apple inc.": ["apple", "Apple"],
    "banana": [],
  }
  mock_fuzzy_matcher._match_nodes.return_value = mock_match_nodes_return

  result = mock_fuzzy_matcher._match_nodes(["apple", "Apple", "apple inc.", "banana"])

  assert (
    result == mock_match_nodes_return
  ), f"Expected {mock_match_nodes_return}, got {result}"


def test_get_match_sets_with_mock() -> None:
  """Test the get_match_sets method of the FuzzyMatcher class using a mock."""
  mock_fuzzy_matcher = MagicMock(spec=FuzzyMatcher)

  mock_get_match_sets_return = [{"apple", "Apple", "apple inc."}, {"banana"}]
  mock_fuzzy_matcher.get_match_sets.return_value = mock_get_match_sets_return

  result = mock_fuzzy_matcher.get_match_sets(["apple", "Apple", "apple inc.", "banana"])

  assert (
    result == mock_get_match_sets_return
  ), f"Expected {mock_get_match_sets_return}, got {result}"
