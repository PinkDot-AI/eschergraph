from __future__ import annotations

import os
from typing import Optional
from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest

from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.exceptions import CredentialException
from eschergraph.graph import Graph
from eschergraph.persistence.vector_db import VectorDB


def set_graph_dependencies_creds(
  vector_creds: Optional[list[str]] = None,
  model_creds: Optional[list[str]] = None,
  reranker_creds: Optional[list[str]] = None,
) -> tuple[MagicMock, MagicMock, MagicMock]:
  vector_mock: MagicMock = MagicMock(spec=VectorDB)
  model_mock: MagicMock = MagicMock(spec=ModelProvider)
  reranker_mock: MagicMock = MagicMock(spec=Reranker)

  if not vector_creds:
    vector_creds = []
  if not model_creds:
    model_creds = []
  if not reranker_creds:
    reranker_creds = []

  vector_mock.required_credentials = vector_creds
  model_mock.required_credentials = model_creds
  reranker_mock.required_credentials = reranker_creds

  return vector_mock, model_mock, reranker_mock


def test_default_creation(graph_unit: Graph) -> None:
  assert isinstance(graph_unit, Graph)


def test_api_keys_not_in_string_format(mock_repository: Mock) -> None:
  vector, reranker, model = set_graph_dependencies_creds()
  with pytest.raises(TypeError):
    Graph(
      model=model,
      vector_db=vector,
      reranker=reranker,
      wrong_key=12,  # type: ignore
      repository=mock_repository,
    )


def test_no_api_keys_provided_and_needed(mock_repository: Mock) -> None:
  vector, reranker, model = set_graph_dependencies_creds(
    vector_creds=["EMBEDDING_API_KEY"]
  )
  with pytest.raises(CredentialException):
    Graph(
      model=model,
      vector_db=vector,
      reranker=reranker,
      repository=mock_repository,
    )


def test_api_keys_provided_not_complete(mock_repository: Mock) -> None:
  vector, reranker, model = set_graph_dependencies_creds(
    vector_creds=["EMBEDDING_API_KEY"], model_creds=["LLM_API_KEY"]
  )
  with pytest.raises(CredentialException):
    Graph(
      model=model,
      vector_db=vector,
      reranker=reranker,
      repository=mock_repository,
      embedding_api_key="key12345",
    )


def test_api_keys_provided_complete(mock_repository: Mock) -> None:
  cred_keys: set[str] = {"EMBEDDING_API_KEY", "LLM_API_KEY", "RERANKER_API_KEY"}
  keys: set[str] = {"key12345", "model123", "reranker_key"}

  # Assert that the keys are missing at the start
  for key in cred_keys:
    assert not key in os.environ

  vector, reranker, model = set_graph_dependencies_creds(
    vector_creds=["EMBEDDING_API_KEY"],
    model_creds=["LLM_API_KEY"],
    reranker_creds=["RERANKER_API_KEY"],
  )
  graph: Graph = Graph(
    model=model,
    vector_db=vector,
    reranker=reranker,
    repository=mock_repository,
    embedding_api_key="key12345",
    llm_api_key="model123",
    reranker_api_key="reranker_key",
  )
  assert set(graph.credentials.keys()) == cred_keys
  assert set(graph.credentials.values()) == keys

  for key in cred_keys:
    assert key in os.environ
