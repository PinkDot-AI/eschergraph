from __future__ import annotations

import random
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.reranker import RerankerResult
from eschergraph.config import MAIN_COLLECTION
from eschergraph.graph.graph import Graph
from eschergraph.graph.search.quick_search import quick_search
from eschergraph.graph.search.quick_search import RAGAnswer
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes
from eschergraph.persistence.vector_db.vector_search_result import VectorSearchResult
from tests.persistence.vector_db.help import generate_vector_search_results

RAG_SEARCH = "search/question_with_context.jinja"


def test_quick_search_empty_query(graph_unit: Graph) -> None:
  RAGanswer: RAGAnswer = quick_search(graph_unit, "")
  assert RAGanswer.answer == "please ask a question"


def test_quick_search_no_attributes_found(graph_unit: Graph) -> None:
  with patch(
    "eschergraph.graph.search.quick_search.get_attributes_search", return_value=[]
  ):
    graph_unit.model.get_plain_response.return_value = "No results found"
    RAGanswer: RAGAnswer = quick_search(graph_unit, "test query")
    assert RAGanswer.answer == "No results found"
    graph_unit.model.get_plain_response.assert_called_with(
      process_template(
        RAG_SEARCH,
        data={
          "CONTEXT": "Nothing found in the graph regarding this question!",
          "QUERY": "test query",
        },
      )
    )


def test_rerank_and_filter_no_attributes(graph_unit: Graph) -> None:
  mock_filter_attributes: MagicMock = MagicMock()
  with patch(
    "eschergraph.graph.search.quick_search.filter_attributes", mock_filter_attributes
  ):
    graph_unit.reranker.rerank.return_value = []
    rerank_and_filter_attributes(graph_unit, "test query", [])
    graph_unit.reranker.rerank.assert_called_once_with("test query", [], top_n=0)
    mock_filter_attributes.assert_called_once_with(graph_unit, [], {}, 0.2)


def test_rerank_and_filter_attributes(graph_unit: Graph) -> None:
  attributes_results: list[VectorSearchResult] = generate_vector_search_results(
    num_results=2
  )
  rerank_result: list[RerankerResult] = [
    RerankerResult(
      index=1, relevance_score=random.uniform(0, 1), text=attributes_results[1].chunk
    ),
    RerankerResult(
      index=0, relevance_score=random.uniform(0, 1), text=attributes_results[0].chunk
    ),
  ]
  graph_unit.reranker.rerank.return_value = rerank_result
  mock_filter_attributes: MagicMock = MagicMock()
  with patch(
    "eschergraph.graph.search.quick_search.filter_attributes", mock_filter_attributes
  ):
    rerank_and_filter_attributes(
      graph_unit, "test query", attributes_results, threshold=0.2
    )

  graph_unit.reranker.rerank.assert_called_once_with(
    "test query", [attributes_results[0].chunk, attributes_results[1].chunk], top_n=2
  )
  mock_filter_attributes.assert_called_once_with(
    graph_unit, rerank_result, {r.chunk: r for r in attributes_results}, 0.2
  )


def test_quick_search_with_doc_filter(graph_unit: Graph) -> None:
  doc_filter: list[UUID] = [uuid4() for _ in range(10)]

  quick_search(graph_unit, "test_query", doc_filter=doc_filter)

  graph_unit.vector_db.search.assert_called_once_with(
    query="test_query",
    top_n=40,
    metadata={"level": 0, "document_id": [str(id) for id in doc_filter]},
    collection_name=MAIN_COLLECTION,
  )


def test_quick_search_without_doc_filter(graph_unit: Graph) -> None:
  quick_search(graph_unit, "test_query")

  graph_unit.vector_db.search.assert_called_once_with(
    query="test_query", top_n=40, metadata={"level": 0}, collection_name=MAIN_COLLECTION
  )
