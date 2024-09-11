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
  graph_name: str = "test_graph2"

  graph: Graph = Graph(
    model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI),
    name=graph_name,
  )
  # graph.build(files=TEST_FILE_2)

  # query = "what are the main theams of this document?"
  # r = graph.global_search(query)
  # print('GLOBAL ANSWER')
  # print(r)
  # print()
  # query = "What did Rahel Dette say in a qoute?"
  print(graph.repository.get_all_at_level(0))
  # r = graph.search(query)
  print("QUICK ANSWER")
  # print(r)
  print()


integration_test_building()


def test_search_graph() -> None:
  """Tests the search functionality of a Graph object."""
  t = time.time()
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)
