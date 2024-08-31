from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.graph import Graph
from eschergraph.graph.persistence.adapters.simple_repository.simple_repository import (
  SimpleRepository,
)
from eschergraph.graph.persistence.repository import Repository
from eschergraph.graph.persistence.vector_db.adapters.chromadb import ChromaDB
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB

TEST_FILE_SMALL: str = "./test_files/test_file.pdf"
TEST_FILE_BIG: str = "./test_files/Attention Is All You Need.pdf"


def integration_test_building() -> None:
  """Integration test for building pipeline."""
  # The temporary directory (clean run for each test)
  temp_dir: TemporaryDirectory = TemporaryDirectory()
  temp_path: Path = Path(temp_dir.name)

  # Set up all the graph dependencies
  graph_name: str = "test_graph"
  repository: Repository = SimpleRepository(
    name=graph_name, save_location=temp_path.as_posix()
  )
  chroma: VectorDB = ChromaDB(save_name=graph_name, persistent=False)
  graph: Graph = Graph(
    model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI),
    reranker=JinaReranker(),
    name=graph_name,
    repository=repository,
    vector_db=chroma,
  )
  t = time.time()
  graph.build(files=TEST_FILE_BIG)

  print("processing time", time.time() - t)

  t = time.time()

  query = "what are the main theams of this document?"
  r = graph.global_search(query)
  print(r)
  print("global search time", time.time() - t)
  t = time.time()

  print()
  r = graph.search(query)
  print(r)

  print("quick search time", time.time() - t)

  # Wait a few seconds before cleaning up to open the visuals
  time.sleep(8)

  # Clean up all the persistent data
  temp_dir.cleanup()


integration_test_building()


def test_search_graph() -> None:
  """Tests the search functionality of a Graph object."""
  t = time.time()
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)
