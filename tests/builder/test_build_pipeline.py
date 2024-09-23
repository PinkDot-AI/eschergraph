from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

import pytest

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.graph.node import Node
from eschergraph.persistence import Metadata
from eschergraph.persistence.adapters.simple_repository import SimpleRepository

if TYPE_CHECKING:
  from eschergraph.graph import Graph


@pytest.fixture(scope="function")
def builder_mock() -> BuildPipeline:
  openai_mock = MagicMock(spec=OpenAIProvider)
  jina_mock = MagicMock(spec=JinaReranker)
  return BuildPipeline(model=openai_mock, reranker=jina_mock)


# Mock VisualDocumentElements
mock_figure_1 = VisualDocumentElement(
  content="A bar chart showing sales data",
  caption="Figure 1: Monthly Sales Data",
  save_location="/path/to/figure1.png",
  page_num=1,
  doc_id=UUID("12345678-1234-5678-1234-567812345678"),
  type="figure",
)

mock_figure_2 = VisualDocumentElement(
  content="A line graph of temperature changes",
  caption="Figure 2: Annual Temperature Trends",
  save_location="/path/to/figure2.png",
  page_num=2,
  doc_id=UUID("87654321-4321-8765-4321-876543210987"),
  type="figure",
)

mock_figure_3 = VisualDocumentElement(
  content="A pie chart of market share",
  caption=None,
  save_location="/path/to/figure3.png",
  page_num=3,
  doc_id=UUID("11111111-2222-3333-4444-555555555555"),
  type="figure",
)
# Mock VisualDocumentElement for a table
mock_table = VisualDocumentElement(
  content="| Column1 | Column2 |\n|---------|---------||\n| Data1   | Data2   |",
  caption="Table 1: Sample Data",
  save_location="/path/to/table1.png",
  page_num=4,
  doc_id=UUID("22222222-3333-4444-5555-666666666666"),
  type="table",
)


# TODO: refactor to use a mock for the repository
def test_persist_to_graph(
  tmp_path: Path, builder_mock: BuildPipeline, graph_unit: Graph
) -> None:
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  graph_unit.name = "test graph"
  graph_unit.repository = repository

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
  builder_mock._persist_to_graph(graph_unit, build_logs)

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

  # TODO: no method to test the edges yet.
