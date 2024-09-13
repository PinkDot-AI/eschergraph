from __future__ import annotations

import os
from typing import Optional
from uuid import UUID

from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import MAIN_COLLECTION
from eschergraph.exceptions import CredentialException
from eschergraph.exceptions import IllogicalActionException
from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.search.global_search import global_search
from eschergraph.graph.search.quick_search import quick_search
from eschergraph.graph.utils import duplicate_document_check
from eschergraph.graph.utils import get_document_ids_from_filenames
from eschergraph.graph.utils import search_check
from eschergraph.persistence import Document
from eschergraph.persistence import Metadata
from eschergraph.persistence import Repository
from eschergraph.persistence.factory import get_default_repository
from eschergraph.persistence.vector_db import get_vector_db
from eschergraph.persistence.vector_db import VectorDB
from eschergraph.tools.prepare_sync_data import prepare_sync_data
from eschergraph.visualization.dashboard_maker import DashboardData
from eschergraph.visualization.dashboard_maker import DashboardMaker
from eschergraph.visualization.visualizer import Visualizer


class Graph:
  """The EscherGraph graph class."""

  name: str
  model: ModelProvider
  reranker: Reranker
  repository: Repository
  vector_db: VectorDB
  credentials: dict[str, str]

  def __init__(
    self,
    name: str = DEFAULT_GRAPH_NAME,
    reranker: Optional[Reranker] = None,
    model: Optional[ModelProvider] = None,
    repository: Optional[Repository] = None,
    vector_db: Optional[VectorDB] = None,
    **kwargs: str,
  ) -> None:
    """The init method for a graph.

    Creates the graph with all of the tools used. It also manages setting up, and
    verifying the presence of, all credentials that are needed for communication with
    external services.

    Args:
      model (ModelProvider): The LLM model that is used.
      reranker (Reranker): The reranker that is used.
      name (str): The name of the graph (optional).
      repository (Optional[Repository]): The persistent storage that is used for the graph.
      vector_db (Optional[VectorDB]): The vector database that is used.
      **kwargs (dict[str, str]): The credentials as optional keyword arguments.
    """
    self.name = name

    if not reranker:
      reranker = JinaReranker()
    if not model:
      model = OpenAIProvider(model=OpenAIModel.GPT_4o)
    if not repository:
      repository = get_default_repository(name=name)
    if not vector_db:
      vector_db = get_vector_db(save_name=name)

    self.repository = repository
    self.vector_db = vector_db
    self.model = model
    self.reranker = reranker
    self.credentials = {}

    self.credentials = {provider.upper(): cred for provider, cred in kwargs.items()}

    required_creds: set[str] = {
      cred
      for cred_list in [
        self.model.required_credentials,
        self.vector_db.required_credentials,
        self.reranker.required_credentials,
      ]
      for cred in cred_list
    }
    # Check if all the required credentials are present
    # They can be present in both the keyword-arguments or the env variables
    for cred in required_creds:
      if not cred in self.credentials and not os.getenv(cred):
        raise CredentialException(f"The API key: {cred} is missing.")

    # Set all the credentials as env variables (only for Python process)
    # This is the easiest way to make them available to all classes
    for cred, key in self.credentials.items():
      os.environ[cred] = key

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

  def sync_vectordb(self) -> None:
    """Synchronizes the vector database with the latest changes in the repository."""
    # Prepare data for synchronization
    create_main, ids_to_delete = prepare_sync_data(repository=self.repository)

    main_collection: str = MAIN_COLLECTION

    if ids_to_delete:
      self.vector_db.delete_by_ids(ids_to_delete, main_collection)

    if create_main:
      ids, docs, metadatas = zip(*create_main)
      self.vector_db.insert(
        documents=list(docs),
        ids=list(ids),
        metadata=list(metadatas),
        collection_name=main_collection,
      )

  def search(self, query: str, filter_filenames: Optional[list[str]] = None) -> str:
    """Executes a search query using a vector database and a specified model.

    Args:
      query (str): The search query as a string.
      filter_filenames(Optional[list[str]]): An optional list of filenames to search in. If not provided,
        all documents are included.

    Returns:
      The result of the search, typically a string that represents the most relevant information or document found by the search.
    """
    if not search_check(self.repository):
      raise IllogicalActionException("You cannot search a graph before building it")

    doc_filter: list[UUID] | None = None
    if filter_filenames:
      doc_filter = get_document_ids_from_filenames(
        filenames=filter_filenames, repository=self.repository
      )

    return quick_search(graph=self, query=query, doc_filter=doc_filter)

  def global_search(
    self, query: str, filter_filenames: Optional[list[str]] = None
  ) -> str:
    """Executes a search query using a vector database and a specified model on the upper layers of the graph.

    Args:
      query (str): The search query as a string.
      filter_filenames(Optional[list[str]]): An optional list of filenames to search in. If not provided,
        all documents are included.

    Returns:
      str: The result of the search, is a string
    """
    if not search_check(self.repository):
      raise IllogicalActionException("You cannot search a graph before building it")

    doc_filter: list[UUID] | None = None
    if filter_filenames:
      doc_filter = get_document_ids_from_filenames(
        filenames=filter_filenames, repository=self.repository
      )

    return global_search(graph=self, query=query, doc_filter=doc_filter)

  def build(self, files: str | list[str]) -> Graph:
    """Build a graph from the given files.

    Args:
        files (str | list[str]): A single file path or a list of file paths to process.
        always_approve (bool, optional): If True, skips user approval. Defaults to False.

    Returns:
        Graph: The built graph object.
    """
    # Prevent circular import errors
    from eschergraph.builder.build_pipeline import BuildPipeline
    from eschergraph.builder.building_tools import BuildingTools

    file_list: list[str] = [files] if isinstance(files, str) else files

    # Check if the documents already exist
    duplicate_document_check(file_list, self.repository)

    chunks, document_data, total_tokens = BuildingTools.process_files(file_list)

    BuildingTools.display_build_info(chunks, total_tokens, model=self.model)

    # Build graph
    builder = BuildPipeline(model=self.model, reranker=self.reranker)
    builder.run(chunks=chunks, graph=self)

    # Add document data objects to the repository
    for doc_data in document_data:
      self.repository.add_document(document=doc_data)

    return self

  def dashboard(self) -> None:
    """Gathers data and visualizes the dashboard using DashboardMaker."""
    data: DashboardData = DashboardMaker.gather_data(graph=self)

    DashboardMaker.visualizer_print(data)

  def visualize(self) -> None:
    """Generate a plot of the graph's level 0 and level 1."""
    Visualizer.visualize_graph(self, level=0, save_location=f"{self.name}_level_0.html")
    Visualizer.visualize_graph(self, level=1, save_location=f"{self.name}_level_1.html")

  def get_all_documents(self) -> list[Document]:
    """Get a list of all documents currently in the graph.

    Returns:
      list[Document]: A list of documents.
    """
    return self.repository.get_all_documents()
