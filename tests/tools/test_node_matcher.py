from __future__ import annotations

from unittest.mock import MagicMock

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
  assert node_matcher_mock.model.get_json_response(prompt="test") == mock_response
  suggested_match = {"Lennart", "Lennart Timmermans", "Patrick", "Patrick Timmermans"}

  result = node_matcher_mock._get_unique_nodes_gpt(suggested_match)
  assert result == mock_response, f"Expected {mock_response}, but got {result}"
  expected_prompt = process_template(
    JSON_UNIQUE_NODES, data={"entities": ", ".join(suggested_match)}
  )
  # Check if get_json_response was called exactly twice
  assert node_matcher_mock.model.get_json_response.call_count == 2, (
    f"Expected get_json_response to be called twice, "
    f"but it was called {node_matcher_mock.model.get_json_response.call_count} times"
  )

  # Verify the prompt passed in the calls
  node_matcher_mock.model.get_json_response.assert_called_with(prompt=expected_prompt)
