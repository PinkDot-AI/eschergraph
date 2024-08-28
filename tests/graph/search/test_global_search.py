from __future__ import annotations

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from eschergraph.agents.reranker import RerankerResult
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.property import Property
from eschergraph.graph.search.global_search import extract_entities_from
from eschergraph.graph.search.global_search import order_properties
from eschergraph.graph.search.global_search import retrieve_key_properties
from eschergraph.graph.search.global_search import retrieve_similar_properties

MagicMockTuple = tuple[
  MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock
]


@pytest.fixture
def setup_mocks() -> MagicMockTuple:
  mock_llm = MagicMock()
  mock_graph = MagicMock()
  mock_graph.repository.get_max_level.return_value = 3

  mock_node_1 = MagicMock()
  mock_node_1.properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    ),
    Property(
      description="Explanation 3", repository=mock_graph.repository, node=mock_node_1
    ),
  ]
  mock_node_2 = MagicMock()
  mock_node_2.properties = [
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    ),
    Property(
      description="Explanation 4", repository=mock_graph.repository, node=mock_node_2
    ),
  ]
  mock_embedder = MagicMock()
  mock_embedder.get_embedding.return_value = [[0.1, 0.2, 0.3]]
  mock_vecdb = MagicMock()
  mock_vecdb.search.return_value = [{"id": "mock-node-id"}]
  mock_vecdb.format_search_results.return_value = [{"id": "mock-node-id"}]
  mock_reranker = MagicMock()
  mock_reranker.rerank.return_value = [
    RerankerResult(0, 0.8, "Text"),
    RerankerResult(1, 0.7, "Text"),
  ]
  mock_node = MagicMock()
  mock_node.properties = [
    Property(
      description="Mock Explanation 1", repository=mock_graph.repository, node=mock_node
    ),
    Property(
      description="Mock Explanation 2", repository=mock_graph.repository, node=mock_node
    ),
  ]
  mock_graph.repository.get_node_by_id.return_value = mock_node
  return (
    mock_llm,
    mock_node_1,
    mock_node_2,
    mock_graph,
    mock_embedder,
    mock_vecdb,
    mock_reranker,
    mock_node,
  )


def test_correct_entity_extraction(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  entities = {"entities": ["entity1", "entity2", "entity3"]}
  mock_llm.get_json_response.return_value = entities
  result = extract_entities_from("Find entities in this query.", mock_llm)
  assert result == entities["entities"]


def test_empty_response_raises_exception(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  mock_llm.get_json_response.return_value = None
  with pytest.raises(ExternalProviderException):
    extract_entities_from("Find entities in this query.", mock_llm)


def test_invalid_json_raises_value_error(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  mock_llm.get_json_response.return_value = "not a json"
  with pytest.raises(ExternalProviderException):
    extract_entities_from("Find entities in this query.", mock_llm)


def test_non_list_json_raises_value_error(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  mock_llm.get_json_response.return_value = {"entity": "not a list"}
  with pytest.raises(ExternalProviderException):
    extract_entities_from("Find entities in this query.", mock_llm)


def test_list_with_non_string_elements_raises_value_error(
  setup_mocks: MagicMockTuple,
) -> None:
  mock_llm, *_ = setup_mocks
  mock_llm.get_json_response.return_value = json.dumps(["entity1", 42, "entity3"])
  with pytest.raises(ExternalProviderException):
    extract_entities_from("Find entities in this query.", mock_llm)


def test_empty_list_response(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  mock_llm.get_json_response.return_value = {"entities": []}
  result = extract_entities_from("Find entities in this query.", mock_llm)
  assert len(result) == 0


def test_correct_ordering_of_properties(setup_mocks: MagicMockTuple) -> None:
  mock_llm, _, _, mock_graph, *_ = setup_mocks
  properties_json = [{"explanation": "Explanation 1"}, {"explanation": "Explanation 2"}]
  mock_node = MagicMock()
  mock_node.properties_to_json.return_value = json.dumps(properties_json)
  mock_llm.get_json_response.return_value = properties_json
  result = order_properties(mock_node, mock_llm)
  expected_properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node
    ),
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node
    ),
  ]
  assert result == expected_properties


def test_empty_properties_response(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  mock_node = MagicMock()
  mock_node.properties_to_json.return_value = json.dumps([])
  mock_llm.get_json_response.return_value = []
  result = order_properties(mock_node, mock_llm)
  assert result == []


def test_invalid_json_structure_raises_error(setup_mocks: MagicMockTuple) -> None:
  mock_llm, *_ = setup_mocks
  mock_node = MagicMock()
  mock_node.properties_to_json.return_value = json.dumps([])
  mock_llm.get_json_response.return_value = {"invalid_key": []}
  with pytest.raises(ExternalProviderException):
    order_properties(mock_node, mock_llm)


def test_empty_response_raises_exception_in_order_properties(
  setup_mocks: MagicMockTuple,
) -> None:
  mock_llm, *_ = setup_mocks
  mock_node = MagicMock()
  mock_llm.get_json_response.return_value = None
  with pytest.raises(ExternalProviderException):
    order_properties(mock_node, mock_llm)


def test_retrieve_top_n_sorted_properties(setup_mocks: MagicMockTuple) -> None:
  mock_llm, mock_node_1, mock_node_2, mock_graph, *_ = setup_mocks
  mock_graph.repository.get_max_level.return_value = 2
  mock_graph.repository.get_all_at_level.return_value = [mock_node_1, mock_node_2]
  mock_node_1.properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    )
  ]
  mock_node_2.properties = [
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    )
  ]
  result = retrieve_key_properties(mock_graph, mock_llm, n=1, sorted=True)
  expected_properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    ),
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    ),
  ]
  assert result == expected_properties


def test_retrieve_top_n_unsorted_properties(setup_mocks: MagicMockTuple) -> None:
  mock_llm, mock_node_1, mock_node_2, mock_graph, *_ = setup_mocks
  mock_graph.repository.get_max_level.return_value = 2
  mock_graph.repository.get_all_at_level.return_value = [mock_node_1, mock_node_2]
  mock_llm.max_threads = 2
  mock_node_1.properties = None
  mock_node_2.properties = None
  mock_node_1.order_properties.return_value = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    )
  ]
  mock_node_2.order_properties.return_value = [
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    )
  ]
  with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
    mock_executor.return_value.__enter__.return_value.map.return_value = [
      mock_node_1.order_properties.return_value,
      mock_node_2.order_properties.return_value,
    ]
    result = retrieve_key_properties(mock_graph, mock_llm, n=1, sorted=False)
  expected_properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    ),
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    ),
  ]
  assert result == expected_properties


def test_retrieve_key_properties_with_specified_level(
  setup_mocks: MagicMockTuple,
) -> None:
  mock_llm, mock_node_1, _, mock_graph, *_ = setup_mocks
  mock_graph.repository.get_all_at_level.return_value = [mock_node_1]
  mock_node_1.properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    )
  ]
  result = retrieve_key_properties(mock_graph, mock_llm, level=1, n=1, sorted=True)
  expected_properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    )
  ]
  assert result == expected_properties


def test_empty_properties_returned_when_no_properties_present(
  setup_mocks: MagicMockTuple,
) -> None:
  mock_llm, mock_node_1, _, mock_graph, *_ = setup_mocks
  mock_graph.repository.get_max_level.return_value = 2
  mock_graph.repository.get_all_at_level.return_value = [mock_node_1]
  mock_node_1.properties = []
  result = retrieve_key_properties(mock_graph, mock_llm, n=1, sorted=True)
  assert result == []


def test_retrieve_key_properties_with_unsorted_nodes_and_custom_n(
  setup_mocks: MagicMockTuple,
) -> None:
  mock_llm, mock_node_1, mock_node_2, mock_graph, *_ = setup_mocks
  mock_graph.repository.get_max_level.return_value = 2
  mock_graph.repository.get_all_at_level.return_value = [mock_node_1, mock_node_2]
  mock_llm.max_threads = 2
  mock_node_1.order_properties.return_value = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    ),
    Property(
      description="Explanation 3", repository=mock_graph.repository, node=mock_node_1
    ),
  ]
  mock_node_2.order_properties.return_value = [
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    ),
    Property(
      description="Explanation 4", repository=mock_graph.repository, node=mock_node_2
    ),
  ]
  with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
    mock_executor.return_value.__enter__.return_value.map.return_value = [
      mock_node_1.order_properties.return_value,
      mock_node_2.order_properties.return_value,
    ]
    result = retrieve_key_properties(mock_graph, mock_llm, n=2, sorted=False)
  expected_properties = [
    Property(
      description="Explanation 1", repository=mock_graph.repository, node=mock_node_1
    ),
    Property(
      description="Explanation 3", repository=mock_graph.repository, node=mock_node_1
    ),
    Property(
      description="Explanation 2", repository=mock_graph.repository, node=mock_node_2
    ),
    Property(
      description="Explanation 4", repository=mock_graph.repository, node=mock_node_2
    ),
  ]
  assert result == expected_properties


def test_retrieve_similar_properties_success(setup_mocks: MagicMockTuple) -> None:
  (
    _,
    _,
    _,
    mock_graph,
    mock_embedder,
    mock_vecdb,
    mock_reranker,
    mock_node,
  ) = setup_mocks
  query = "This is a test query."
  result = retrieve_similar_properties(
    mock_graph, query, mock_vecdb, "Collection name", mock_reranker
  )
  expected_result = [
    Property(
      description="Mock Explanation 1",
      repository=mock_graph.repository,
      node=mock_node,
    ),
    Property(
      description="Mock Explanation 2",
      repository=mock_graph.repository,
      node=mock_node,
    ),
  ]
  assert result == expected_result
