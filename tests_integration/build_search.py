from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv

from eschergraph import Graph
from eschergraph.agents import OpenAIModel
from eschergraph.agents import OpenAIProvider
from eschergraph.persistence import Repository
from eschergraph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.persistence.document import Document
from eschergraph.persistence.vector_db import VectorDB
from eschergraph.persistence.vector_db.adapters.chromadb import ChromaDB
from eschergraph.visualization import Visualizer

TEST_FILE: str = "./test_files/Attention Is All You Need.pdf"

# Load all the credentials
load_dotenv()


def build_graph() -> None:
  # The temporary directory (clean run for each test)
  temp_dir: TemporaryDirectory = TemporaryDirectory()
  temp_path: Path = Path(temp_dir.name)

  # Set up all the graph dependencies
  graph_name: str = "test_graph"
  repository: Repository = SimpleRepository(
    name=graph_name, save_location=temp_path.as_posix()
  )
  chroma: VectorDB = ChromaDB(
    save_name=graph_name,
    persistent=False,
    embedding_model=OpenAIProvider(model=OpenAIModel.TEXT_EMBEDDING_LARGE),
  )
  graph: Graph = Graph(
    name=graph_name,
    repository=repository,
    vector_db=chroma,
    model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI),
  )

  # Build the graph
  graph.build(TEST_FILE)

  Visualizer.visualize_graph(
    graph, level=0, save_location=temp_path.as_posix() + "/level_0.html"
  )
  Visualizer.visualize_graph(
    graph, level=1, save_location=temp_path.as_posix() + "/level_1.html"
  )
  Visualizer.visualize_graph(
    graph, level=2, save_location=temp_path.as_posix() + "/level_2.html"
  )

  documents: list[Document] = graph.get_all_documents()

  print("The document currently in the graph: ")
  print(documents)
  doc_name: str = documents[0].name

  answer = graph.search("Who are the architects?", filter_filenames=[doc_name])
  print(answer)

  global_answer = graph.global_search(
    "What are the key points?", filter_filenames=[doc_name]
  )
  print(global_answer)

  graph.dashboard()

  # Wait a few seconds before cleaning up to open the visuals
  time.sleep(10)

  # Clean up all the persistent data
  temp_dir.cleanup()


if __name__ == "__main__":
  build_graph()
