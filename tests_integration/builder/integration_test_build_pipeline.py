from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.graph import Graph
from eschergraph.tools.reader import Reader

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
jina_api_key = os.getenv("JINA_API_KEY")


def integration_test_building() -> None:
  """Integration test for building pipeline."""
  required_credentials = [openai_api_key, jina_api_key]
  openai_client = OpenAIProvider(
    model=OpenAIModel.GPT_4o_MINI, required_credentials=required_credentials
  )
  reranker_client = JinaReranker(required_credentials=required_credentials)
  file_path = "test_files/test_file.pdf"
  t = time.time()
  reader: Reader = Reader(file_location=file_path, multimodal=False)
  reader.parse()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)

  builder = BuildPipeline(model=openai_client, reranker=reranker_client)
  builder.run(chunks=reader.chunks, graph=graph)

  print("processing time", time.time() - t)
  query = "what is the oig?"

  r = graph.search(query=query)
  print("searching time", time.time() - t)
  print(r)


integration_test_building()


def test_search_graph() -> None:
  """Tests the search functionality of a Graph object."""
  t = time.time()
  openai_client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)
  reranker_client = JinaReranker()
  graph: Graph = Graph(name="my graph", model=openai_client, reranker=reranker_client)
