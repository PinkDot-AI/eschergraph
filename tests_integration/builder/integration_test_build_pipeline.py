from __future__ import annotations

import time

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.graph import Graph

TEST_FILE_SMALL: str = "./test_files/test_file.pdf"
TEST_FILE_BIG: str = "./test_files/Attention Is All You Need.pdf"
TEST_FILE_2: str = "./test_files/test_file_2.pdf"


def integration_test_building() -> None:
  # Set up all the graph dependencies
  graph_name: str = "test_graph"
  graph: Graph = Graph(
    name=graph_name,
    model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI),
  )

  # Build the graph
  graph.build(files=TEST_FILE_2, multi_modal=True)

  query = "What does the Figure 1. Generic Risk Model with Key Risk Factors illustrate?"
  answer = graph.search(query)
  print(answer.answer)
  print(answer.visuals)
  print("\n-------------\n")
  query = "What does the Figure 1 illustrate?"
  answer = graph.search(query)
  print(answer.answer)
  print(answer.visuals)


integration_test_building()


def test_search_graph() -> None:
  """Tests the search functionality of a Graph object."""
  t = time.time()
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)
