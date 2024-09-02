from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import pytest

from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.agents.reranker import RerankerResult
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.graph.persistence.metadata import Metadata
from eschergraph.tools.node_matcher import NodeMatcher


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
  suggested_match: set[str] = {
    "Lennart",
    "Lennart Timmermans",
    "Patrick",
    "Patrick Timmermans",
  }

  result = node_matcher_mock._get_unique_nodes_gpt(suggested_match)
  assert result == mock_response, f"Expected {mock_response}, but got {result}"
  # Check if get_json_response was called exactly once
  assert node_matcher_mock.model.get_json_response.call_count == 1, (
    f"Expected get_json_response to be called once, "
    f"but it was called {node_matcher_mock.model.get_json_response.call_count} times"
  )


def test_assign_node(node_matcher_mock: NodeMatcher) -> None:
  node_matcher_mock.reranker.rerank.return_value = [
    RerankerResult(index=1, relevance_score=1.8, text="Patrick Timmermans---mock test")
  ]
  description = "Some description about Patrick"
  node_info = {
    "Lennart Timmermans": ["description1", "description2"],
    "Patrick Timmermans": ["description3", "description4"],
  }

  # Call the method
  result = node_matcher_mock._assign_node(description, node_info)

  # Assert the expected result
  assert (
    result == "Patrick Timmermans"
  ), f"Expected 'Patrick Timmermans' but got '{result}'"


def test_collection_node_info(node_matcher_mock: NodeMatcher) -> None:
  # Set up the build_log input with one entry
  build_log = [
    BuildLog(
      metadata=Metadata(document_id=uuid4(), chunk_id=4),
      nodes=[
        NodeExt(name="node 1", description="node 1 is cool"),
        NodeExt(name="node 2", description="node 2 is medium"),
      ],
      edges=[
        EdgeExt(source="node 1", target="node 2", relationship="node 1 loves node 2")
      ],
      properties=[
        PropertyExt(
          entity_name="node 1",
          properties=["node 1 is very cool", "node 1 has many friends"],
        )
      ],
      chunk_text="node 1 is in love with node 2. Node 1 is cool, very cool and has many friends. Node 2 is medium",
    )
  ]
  nodes = ["node 1"]

  # Call the method
  result = node_matcher_mock._collect_node_info(build_log, nodes)

  # Define the expected output
  expected_result = {
    "node 1": [
      "node 1 is cool",
      "node 1 loves node 2",
      "node 1 is very cool",
      "node 1 has many friends",
    ]
  }

  # Assert that the result matches the expected output
  assert result == expected_result, f"Expected {expected_result} but got {result}"


def test_handle_merge(node_matcher_mock: NodeMatcher) -> None:
  # Patch the _get_unique_nodes method at the class level
  with patch(
    "eschergraph.tools.node_matcher.NodeMatcher._get_unique_nodes",
    return_value=[
      {
        "entities": [
          {
            "name": "Lennart Timmermans",
            "merged entities": ["Lennart Timmermans", "Lennart", "Timmermans"],
          },
          {
            "name": "Patrick Timmermans",
            "merged entities": ["Patrick Timmermans", "Timmermans"],
          },
        ]
      }
    ],
  ) as mock_get_unique_nodes:
    # Patch the _build_entity_to_nodes_map method at the class level
    with patch(
      "eschergraph.tools.node_matcher.NodeMatcher._build_entity_to_nodes_map",
      return_value=(
        {"Lennart Timmermans", "Patrick Timmermans"},
        {"Lennart Timmermans": "Lennart", "Patrick Timmermans": "Patrick"},
      ),
    ) as mock_build_entity_to_nodes_map:
      # Patch the _process_entities_for_logs method at the class level
      with patch(
        "eschergraph.tools.node_matcher.NodeMatcher._process_entities_for_logs",
        return_value=None,
      ) as mock_process_entities_for_logs:
        # Prepare the suggested_matches input
        suggested_matches = [
          {"Lennart", "Lennart Timmermans", "Patrick", "Patrick Timmermans"}
        ]

        # Mock building_logs since it's only passed through
        building_logs = MagicMock()

        # Call the method under test
        result = node_matcher_mock.handle_merge(building_logs, suggested_matches)

        # Assert that _get_unique_nodes was called with the correct arguments
        mock_get_unique_nodes.assert_called_once_with(suggested_matches)

        # Assert that _build_entity_to_nodes_map was called correctly
        mock_build_entity_to_nodes_map.assert_called_once_with(
          mock_get_unique_nodes.return_value[0]
        )

        # Assert that _process_entities_for_logs was called correctly
        mock_process_entities_for_logs.assert_called_once_with(
          building_logs, mock_build_entity_to_nodes_map.return_value[1]
        )

        # Assert that the result is the passed building_logs (as it should be unmodified)
        assert result == building_logs, "The building_logs should be returned as is"
