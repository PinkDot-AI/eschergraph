from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv

from eschergraph import Graph
from eschergraph.agents import OpenAIModel
from eschergraph.agents import OpenAIProvider
from eschergraph.builder.reader.reader import Reader
from eschergraph.persistence import Repository
from eschergraph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.persistence.vector_db import VectorDB
from eschergraph.persistence.vector_db.adapters.chromadb import ChromaDB
from eschergraph.tools.community_builder import _extract_main_topics
from eschergraph.tools.community_builder import _extract_topic_relations
from eschergraph.tools.community_builder import MainTopic
from eschergraph.tools.community_builder import TopicRelations

TEST_FILE: str = "./test_files/Attention Is All You Need.pdf"

# Load all the credentials
load_dotenv()


def get_main_topics() -> None:
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
  reader: Reader = Reader(file_location=TEST_FILE)
  reader.parse()
  main_topics: list[MainTopic] = _extract_main_topics(graph, reader.full_text)
  print([topic.name for topic in main_topics])
  topic_relations: list[TopicRelations] = _extract_topic_relations(
    graph, main_topics, reader.full_text
  )
  print([rel.model_dump_json() + "\n" for rel in topic_relations])


if __name__ == "__main__":
  get_main_topics()
