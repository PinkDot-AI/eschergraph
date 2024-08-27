from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.graph.graph import Graph
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
    builder = BuildPipeline(model=client, reranker=JinaReranker(api_key=jina_api_key))
  graph: Graph = Graph(name="my graph")

  builder.run(chunks=reader.chunks, graph=graph)

  print("processing time", time.time() - t)


# integration_test_building()
