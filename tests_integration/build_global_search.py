from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder import BuildPipeline
from eschergraph.graph import Graph
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.vector_db import VectorDB
from eschergraph.graph.persistence.vector_db.adapters.chromadb import ChromaDB
from eschergraph.tools.reader import Chunk
from eschergraph.tools.reader import Reader
from eschergraph.visualization import Visualizer

TEST_FILE: str = "./test_files/test_file.pdf"

# Load all the credentials
load_dotenv()


def build_global_search() -> None:
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

  # Read and parse the document
  chunks: list[Chunk] = Reader(file_location=TEST_FILE).parse()

  # Build the graph
  build_pipeline: BuildPipeline = BuildPipeline(
    model=graph.model, reranker=graph.reranker
  )
  build_pipeline.run(chunks, graph)
  Visualizer.visualize_graph(
    graph, level=0, save_location=temp_path.as_posix() + "/level0.html"
  )
  Visualizer.visualize_graph(
    graph, level=1, save_location=temp_path.as_posix() + "/level1.html"
  )

  # Wait a few seconds before cleaning up to open the visuals
  time.sleep(10)

  # Clean up all the persistent data
  temp_dir.cleanup()


if __name__ == "__main__":
  build_global_search()
