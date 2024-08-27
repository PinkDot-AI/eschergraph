from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.tools.node_matcher import NodeMatcher

JSON_UNIQUE_NODES = "identifying_nodes.jinja"


@pytest.fixture(scope="function")
def node_matcher_mock() -> NodeMatcher:
  mock_response = {
    "entities": [
      {
        "name": "Lennart Timmermans",
        "merged entities": ["Lennart Timmermans", "Lennart"],
      },
      {
        "name": "Patrick Timmermans",
        "merged entities": ["Patrick Timmermans", "Patrick"],
      },
    ]
  }
  model_mock = MagicMock(ModelProvider)
  reranker_mock = MagicMock(Reranker)
  model_mock.get_json_response.return_value = mock_response

  return NodeMatcher(model=model_mock, reranker=reranker_mock)


def test_get_unique_nodes_gpt(node_matcher_mock: NodeMatcher) -> None:
  with patch.object(
    node_matcher_mock.model, "get_json_response", MagicMock()
  ) as mock_get_json_response:
    # Define the mock response
    mock_response = {
      "entities": [
        {
          "name": "Lennart Timmermans",
          "merged_entities": ["Lennart Timmermans", "Lennart"],
        },
        {
          "name": "Patrick Timmermans",
          "merged_entities": ["Patrick Timmermans", "Patrick"],
        },
      ]
    }

    # Set what the mock should return
    mock_get_json_response.return_value = mock_response

    # Define the suggested match set
    suggested_match = {"Lennart", "Lennart Timmermans", "Patrick", "Patrick Timmermans"}

    # Call the function under test
    result = node_matcher_mock._get_unique_nodes_gpt(suggested_match)

    # Assertions
    assert result == mock_response, f"Expected {mock_response}, but got {result}"
    expected_prompt = process_template(
      JSON_UNIQUE_NODES, data={"entities": ", ".join(suggested_match)}
    )

    # Check if get_json_response was called exactly twice
    assert mock_get_json_response.call_count == 2, (
      f"Expected get_json_response to be called twice, "
      f"but it was called {mock_get_json_response.call_count} times"
    )

    # Optionally, check if it was called with specific arguments
    mock_get_json_response.assert_called_with(expected_prompt)
