from __future__ import annotations

import time

from dotenv import load_dotenv

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.graph import Graph

load_dotenv()


def integration_test_building() -> None:
  """Integration test for building pipeline."""
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  file_path = "test_files/Attention is All You Need.pdf"
  t = time.time()

  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)

  graph.build(files=file_path)
  print("processing time", time.time() - t)


integration_test_building()


def test_search_graph() -> None:
  """Tests the search functionality of a Graph object."""
  t = time.time()
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)
