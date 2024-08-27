from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.graph.graph import Graph
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB
from eschergraph.tools.reader import Reader

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
jina_api_key = os.getenv("JINA_API_KEY")


def integration_test_building() -> None:
  if openai_api_key:
    client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI, api_key=openai_api_key)
  file_path = "test_files/test_file.pdf"
  t = time.time()
  reader: Reader = Reader(file_location=file_path, multimodal=False)
  reader.parse()
  if jina_api_key:
    builder = BuildPipeline(model=client, reranker=JinaReranker())
  graph: Graph = Graph(name="my graph")

  builder.run(chunks=reader.chunks, graph=graph)

  print("processing time", time.time() - t)


# integration_test_building()
@pytest.fixture(scope="function")
def builder_mock() -> BuildPipeline:
  openai_mock = MagicMock(spec=OpenAIProvider)
  jina_mock = MagicMock(spec=JinaReranker)
  return BuildPipeline(model=openai_mock, reranker=jina_mock)


def test_persist_to_graph(tmp_path: Path, builder_mock: BuildPipeline):
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  # Mock the repository
  mock_vector_db = MagicMock(spec=VectorDB)
  mock_graph = Graph(name="test graph", repository=repository, vector_db=mock_vector_db)

  # Prepare build logs
  build_logs = [
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
    ),
    BuildLog(
      metadata=Metadata(document_id=uuid4(), chunk_id=4),
      nodes=[NodeExt(name="node 2", description="node 2 does not like langchain")],
      edges=[],
      properties=[],
      chunk_text="mock",
    ),
  ]

  # Call the method under test
  builder_mock._persist_to_graph(mock_graph, build_logs)

  # Fetch all nodes from the repository
  all_nodes: list[Node] = repository.get_all_at_level(0)
  node_names = [n.name for n in all_nodes]

  # Assert that the correct nodes were added
  assert set(node_names) == {
    "node 1",
    "node 2",
  }, f"Expected nodes {'node 1', 'node 2'}, but got {set(node_names)}"

  # Verify that the properties and edges were correctly added for each node
  for node in all_nodes:
    if node.name == "node 1":
      # Check properties of node 1
      expected_properties = ["node 1 is very cool", "node 1 has many friends"]
      actual_properties = [prop.description for prop in node.properties]
      assert set(actual_properties) == set(
        expected_properties
      ), f"Expected properties {expected_properties}, but got {actual_properties}"

    if node.name == "node 2":
      properties = node.properties
      # Node 2 does not have properties or edges in the second log entry
      assert (
        len(properties) == 0
      ), f"Expected no properties for 'node 2', but got {len(properties)}"

  # TODO no method to test the edges yet.
