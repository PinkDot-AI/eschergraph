from __future__ import annotations

import json
import logging
import os
from typing import Optional
from uuid import UUID

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.exceptions import CredentialException
from eschergraph.exceptions import EdgeDoesNotExistException
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.comm_graph import CommunityGraphResult
from eschergraph.graph.community_alg import get_leidenalg_communities
from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository
from eschergraph.graph.property import Property
from eschergraph.tools.prepare_sync_data import prepare_sync_data

COMMUNITY_TEMPLATE: str = "community_prompt.jinja"
TEMPLATE_IMPORTANCE: str = "search/importance_rank.jinja"
from eschergraph.graph.persistence.vector_db import get_vector_db
from eschergraph.graph.persistence.vector_db import VectorDB


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
      vector_db = get_vector_db()

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

  def sync_vectordb(
    self, collection_name: str = "main_collection", level: int = 0
  ) -> None:
    """Synchronizes the vector database with the latest changes in the repository.

    Args:
        collection_name (str): The name of the vector database collection where documents should be stored.
        level (int, optional): The hierarchical level at which the metadata is being synced. Default is 0.
    """
    # Prepare data for synchronization
    docs, ids, metadata, ids_to_delete = prepare_sync_data(
      repository=self.repository, level=level
    )

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

  def build_community_layer(self, from_level: int, llm: ModelProvider) -> None:
    """Build a community layer in a new level of the graph.

    Args:
        from_level (int): Which level to build on top of.
        llm (Model): LLM to create community reports

    """
    nodes: list[Node] = self.repository.get_all_at_level(from_level)
    comms: CommunityGraphResult = get_leidenalg_communities(nodes)

    # Transform nodes of graph to dict for faster lookup
    node_lookup: dict[UUID, Node] = {nd.id: nd for nd in nodes}
    # Map every node to its community
    node_comm: dict[UUID, int] = {
      nd: idx for idx, comm in enumerate(comms.partitions) for nd in comm
    }

    edges: list[Edge] = []
    # Create an empty community node for each community
    nodes_tmp: dict[int, Node] = {
      idx: self._create_empty_community_node(comms.partitions[idx], from_level + 1)
      for idx in set(node_comm.values())
    }

    # Add edges between community nodes
    for edge_id in comms.edges:
      edge = self.repository.get_edge_by_id(edge_id)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")

      frm: int = node_comm[edge.frm.id]
      to: int = node_comm[edge.to.id]

      # Only use the edges that exist between communities
      if frm == to:
        continue

      new_edge = Edge.create(frm=nodes_tmp[frm], to=nodes_tmp[to], description="")
      edges.append(new_edge)

    for k, v in nodes_tmp.items():
      idx: int = node_comm[v.id]
      prop_format: str = "node_name,property\n" + "\n".join(
        f"{node_lookup[nd_id].name},{prop.description}"
        for nd_id in comms.partitions[idx]
        for prop in node_lookup[nd_id].properties
      )

      edge_relations = self._gather_community_edges(
        self.repository, comms.edges, comms.partitions[idx]
      )
      edge_format: str = "from,to,description\n" + "\n".join(
        f"{ed.frm.name},{ed.to.name},{ed.description}" for ed in edge_relations
      )

      prompt = process_template(
        COMMUNITY_TEMPLATE,
        {
          "relationships": edge_format,
          "properties": prop_format,
        },
      )

      res = llm.get_formatted_response(prompt, {"type": "json_schema"})
      if res is None:
        raise ExternalProviderException("Invalid response from LLM")
      parsed_json = json.loads(res)
      if (
        "title" not in parsed_json
        or "summary" not in parsed_json
        or "findings" not in parsed_json
      ):
        raise ExternalProviderException(
          "LLM JSON Response did not contain correct keys"
        )
      jsonized = json.dumps(parsed_json["findings"], indent=4)
      prompt = process_template(TEMPLATE_IMPORTANCE, {"json_list": jsonized})

      res_reorder = llm.get_formatted_response(
        prompt=prompt, response_format={"type": "json_schema"}
      )
      if res_reorder is None:
        raise ExternalProviderException("Invalid response from LLM for reordering")
      findings = json.loads(res_reorder)
      if not isinstance(findings, list):
        raise ExternalProviderException("Invalid response from LLM for reordering")

      for finding in findings:
        Property.create(nodes_tmp[k], description=finding["explanation"])
      nodes_tmp[k].name = parsed_json["title"]
      nodes_tmp[k].description = parsed_json["summary"]

      self.repository.add(nodes_tmp[k])

    for edge in edges:
      self.repository.add(edge)

    logging.info("Community succesfully added")

  def _create_empty_community_node(self, child_nodes: list[UUID], level: int) -> Node:
    """Create an empty node to be used a community node. Name and description are left empty.

    Args:
        child_nodes (list[UUID]): List of child node ids.
        level (int): At which level the community node will be.

    Returns:
        Node: The newly created node.
    """
    return Node.create(
      name="",
      description="",
      level=level + 1,
      repository=self.repository,
      child_nodes=[
        node
        for node_id in child_nodes
        if (node := self.repository.get_node_by_id(node_id)) and node is not None
      ],
    )

  @staticmethod
  def _gather_community_edges(
    repository: Repository, edges: list[UUID], nodes: list[UUID]
  ) -> list[Edge]:
    """Get all edges that are connected to a node from the node list.

    Args:
        repository (Repository): The repository that is connected with the edges
        edges (list[UUID]): Edges to be filtered.
        nodes (list[UUID]): The nodes to which the edges should be connected

    Returns:
        list[Edge]: A list of the filtered edges.
    """
    node_set = set(nodes)
    comm_edges = []
    for edge_id in edges:
      edge = repository.get_edge_by_id(edge_id)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")
      if edge.frm.id in node_set or edge.to.id in node_set:
        comm_edges.append(edge)

    return comm_edges
