from __future__ import annotations

import time
from typing import cast

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import NodeEdgeExt
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.builder.reader.reader import Chunk
from eschergraph.builder.reader.reader import Reader
from eschergraph.config import JSON_BUILD
from eschergraph.config import JSON_PROPERTY
from eschergraph.graph.graph import Graph
from eschergraph.persistence.metadata import Metadata


def chunk_optimizer():
  # The temporary directory (clean run for each test)

  builder = BuildPipeline(
    model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI), reranker=JinaReranker()
  )
  test_file: str = "test_files/test_file_2.pdf"

  chunks: list[Chunk] = Reader(file_location=test_file, optimal_tokens=400).parse()

  for i in range(2):
    chunk = chunks[i]
    prompt_formatted: str = process_template(JSON_BUILD, {"input_text": chunk.text})

    answer = builder.model.get_json_response(prompt=prompt_formatted)
    json_nodes_edges: NodeEdgeExt = cast(NodeEdgeExt, answer)
    metadata: Metadata = Metadata(document_id=chunk.doc_id, chunk_id=chunk.chunk_id)
    log = BuildLog(
      chunk_text=chunk.text,
      metadata=metadata,
      nodes=json_nodes_edges["entities"],
      edges=json_nodes_edges["relationships"],
    )
    # node properties
    node_names: list[str] = [node["name"] for node in log.nodes]
    if not node_names:
      return

    prompt_formatted: str = process_template(
      JSON_PROPERTY,
      {
        "current_nodes": ", ".join(node_names),
        "input_text": log.chunk_text,
      },
    )
    properties: dict[str, list[dict[str, list[str]]]] = builder.model.get_json_response(
      prompt=prompt_formatted
    )

    print("TEXT")
    print(chunk.text)
    print("EXTRACT")
    print(node_names)
    print(properties)
    print("EDGES")
    for e in log.edges:
      print(e)


TEST_FILE_2 = "test_files/test_file_2.pdf"


def search_check():
  # Set up all the graph dependencies
  graph_name: str = "eschergraph4"

  graph: Graph = Graph(
    model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI),
    name=graph_name,
  )
  # graph.build(files=TEST_FILE_2)

  query = "Who is Mahmood Sher-Jan?"
  r = graph.search(query)
  print(r)


def test_search_graph() -> None:
  """Tests the search functionality of a Graph object."""
  t = time.time()
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)
