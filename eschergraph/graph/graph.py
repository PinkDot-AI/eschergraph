from __future__ import annotations

import os
from typing import Optional

from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.exceptions import CredentialException
from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.document import DocumentData
from eschergraph.graph.persistence.factory import get_default_repository
from eschergraph.graph.persistence.vector_db import get_vector_db
from eschergraph.graph.persistence.vector_db import VectorDB
from eschergraph.graph.search.quick_search import quick_search
from eschergraph.tools.estimator import Estimator
from eschergraph.tools.prepare_sync_data import prepare_sync_data
from eschergraph.tools.reader import Chunk
from eschergraph.tools.reader import Reader


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
    model: ModelProvider,
    reranker: Reranker,
    name: str = DEFAULT_GRAPH_NAME,
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
    self.model = model
    self.reranker = reranker

    if not repository:
      repository = get_default_repository(name=name)
    if not vector_db:
      vector_db = get_vector_db(save_name=name)

    self.repository = repository
    self.vector_db = vector_db
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

  def sync_vectordb(self, collection_name: str = "main_collection") -> None:
    """Synchronizes the vector database with the latest changes in the repository.

    Args:
        collection_name (str): The name of the vector database collection where documents should be stored.
        level (int, optional): The hierarchical level at which the metadata is being synced. Default is 0.
    """
    # Prepare data for synchronization
    docs, ids, metadata, ids_to_delete = prepare_sync_data(repository=self.repository)

    self.vector_db.get_or_create_collection(collection_name)

    # Delete all records marked for deletion
    if ids_to_delete:
      self.vector_db.delete_with_id(ids_to_delete, collection_name)

    # Embed all new or updated entries and insert into the vector database
    if docs:
      self.vector_db.insert(
        documents=docs,
        ids=ids,
        metadata=metadata,
        collection_name=collection_name,
      )

  def search(self, query: str) -> str:
    """Executes a search query using a vector database and a specified model.

    Args:
        query (str): The search query as a string.

    Returns:
        str: The result of the search, typically a string that represents the most relevant information or document found by the search.
    """
    result = quick_search(vector_db=self.vector_db, query=query, model=self.model)
    return result

  def build(self, files: str | list[str], always_approve: bool = False) -> Graph:
    """Build a graph from the given files.

    Args:
        files (str | list[str]): A single file path or a list of file paths to process.
        always_approve (bool, optional): If True, skips user approval. Defaults to False.

    Returns:
        Graph: The built graph object.
    """
    chunks, document_data, total_tokens = self._process_files(files)

    self._display_build_info(chunks, total_tokens)

    if not always_approve and not self._get_user_approval():
      print("Building cancelled.")
      return self

    # Build graph
    builder = BuildPipeline(model=self.model, reranker=self.reranker)
    builder.run(chunks=chunks, graph=self)

    # Add document data to repository
    self.repository.add_document(document_data=document_data)

    return self

  def _process_files(
    self, files: str | list[str]
  ) -> tuple[list[Chunk], list[DocumentData], int]:
    """Process the given files and extract chunks, document data, and total tokens.

    Args:
        files (str | list[str]): A single file path or a list of file paths to process.

    Returns:
        tuple[list[Chunk], list[DocumentData], int]: A tuple containing:
            - A list of Chunk objects
            - A list of DocumentData objects
            - The total number of tokens processed
    """
    chunks: str[Chunk] = []
    document_data: list[DocumentData] = []
    total_tokens: int = 0

    file_list = [files] if isinstance(files, str) else files

    for file in file_list:
      reader = Reader(file_location=file)
      reader.parse()
      chunks.extend(reader.chunks)

      doc_data = DocumentData(
        id=reader.doc_id,
        name=reader.filename,
        chunk_num=len(reader.chunks),
        token_num=reader.total_tokens,
        loss_of_information=None,
      )
      document_data.append(doc_data)
      total_tokens += reader.total_tokens

    return chunks, document_data, total_tokens

  def _display_build_info(self, chunks: list[Chunk], total_tokens: int) -> None:
    """Display information about the graph building process.

    Args:
        chunks (list[Chunk]): The list of chunks to be processed.
        total_tokens (int): The total number of tokens to be processed.
    """
    model_name = self.model.get_model_name()
    estimated_time = Estimator.get_time_indication(
      num_chunks=len(chunks), model=model_name
    )
    estimated_cost = Estimator.get_cost_indication(
      total_tokens=total_tokens, model=model_name
    )
    print("------------------------INFO-------------------------")
    print(
      f"This will parse {len(chunks)} chunks, analyze {total_tokens} tokens\n"
      f"Using {model_name} with an approximate cost of ${estimated_cost:.2f} \n"
      f"Estimated building time is: {estimated_time}\n"
    )

  @staticmethod
  def _get_user_approval() -> bool:
    """Prompt the user for approval to build the graph.

    Returns:
        bool: True if the user approves, False otherwise.
    """
    user_input = input("Press y to build graph - anything to cancel").lower()
    return user_input == "y"
