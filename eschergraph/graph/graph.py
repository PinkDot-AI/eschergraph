from __future__ import annotations

import os

from attrs import define
from attrs import field
from dotenv import load_dotenv

from eschergraph.agents.embedding import Embedding
from eschergraph.agents.providers.openai import ChatGPT
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository
from eschergraph.graph.persistence.vector_db import get_vector_db
from eschergraph.graph.persistence.vector_db import VectorDB
from eschergraph.tools.prepare_sync_data import prepare_sync_data

load_dotenv()


@define
class Graph:
  """The EscherGraph graph class."""

  name: str
  repository: Repository = field(factory=get_default_repository)
  vector_db: VectorDB = field(factory=get_vector_db)
  embedding_model: Embedding | None = field(factory=None)

  def __init__(self) -> None:
    """This is the initializer of the graph class for getting the vectordb."""
    self.vector_db = get_vector_db()
    # Retrieve the API key from the environment
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
      raise ValueError(
        "API key is not set. Please set the OPENAI_API_KEY environment variable."
      )

    # Initialize the embedding model if it's not already provided
    if self.embedding_model is None:
      self.embedding_model = ChatGPT(
        model=OpenAIModel.TEXT_EMBEDDING_LARGE, api_key=api_key
      )

  def add_node(
    self,
    name: str,
    description: str,
    level: int,
    metadata: Metadata,
  ) -> Node:
    """Add a node to the graph.

    After creation, the node is persisted immediately to the repository.
    This is done as no data is saved in the graph object itself.

    Args:
      name (str): The name of the node.
      description (str): A description of the node.
      level (int): The level of the node.
      metadata (Metadata): The metadata of the node.

    Returns:
      The node that has been created.
    """
    node: Node = Node.create(
      name=name,
      description=description,
      level=level,
      repository=self.repository,
      metadata={metadata},
    )

    # Persist the node
    self.repository.add(node)

    return node

  def add_edge(self, frm: Node, to: Node, description: str, metadata: Metadata) -> Edge:
    """Add an edge to the graph.

    The edge is persisted to the repository straight away.

    Args:
      frm (Node): The from node in the edge.
      to (Node): The to node in the edge.
      description (str): A rich description of the relation.
      metadata (Metadata): The metadata of the edge.

    Returns:
      The edge that has been added to the graph.
    """
    edge: Edge = Edge.create(
      frm=frm,
      to=to,
      description=description,
      metadata={metadata},
    )

    # Persist the edge
    self.repository.add(edge)

    return edge

  def sync_vectordb(self, collection_name: str, level: int = 0) -> None:
    """Synchronizes the vector database with the latest changes in the repository.

    Args:
        collection_name (str): The name of the vector database collection where documents should be stored.
        level (int, optional): The hierarchical level at which the metadata is being synced. Default is 0.
    """
    # Prepare data for synchronization
    docs, ids, metadata, ids_to_delete = prepare_sync_data(
      repository=self.repository, level=level
    )

    # Delete all records marked for deletion
    if ids_to_delete:
      self.vector_db.delete_with_id(ids_to_delete, collection_name)

    # Embed all new or updated entries and insert into the vector database
    if docs:
      if self.embedding_model:
        embeddings: list[list[float]] = self.embedding_model.get_embedding(
          list_text=docs
        )

        self.vector_db.insert_documents(
          embeddings=embeddings,
          documents=docs,
          ids=ids,
          metadata=metadata,
          collection_name=collection_name,
        )
