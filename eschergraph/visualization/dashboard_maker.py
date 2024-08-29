from __future__ import annotations

from heapq import nlargest
from typing import Any
from typing import TYPE_CHECKING

from tabulate import tabulate

if TYPE_CHECKING:
  from eschergraph.agents.llm import ModelProvider
  from eschergraph.graph.node import Node
  from eschergraph.graph.persistence import Repository
  from eschergraph.graph.persistence.document import DocumentData


class DashboardMaker:
  """This is a class that holds a functions and logic for the graph dashboard."""

  @staticmethod
  def gather_data(repository: Repository, model: ModelProvider) -> dict[str, Any]:
    """Gathers necessary data for the dashboard.

    Args:
      repository (Repository): is the repository from where to gather the data
      model (ModelProvider): is model used for graph building

    Returns a dictionary with all required information.
    """
    # Get the model type
    llm_model_type = model.get_model_name()
    # TODO: Add embedding and reranker type

    # Gather document and node data
    lower_nodes: list[Node] = repository.get_all_at_level(0)
    communities: list[Node] = repository.get_all_at_level(1)

    # Combine nodes for overall calculations
    all_nodes = lower_nodes + communities

    # Efficiently find the top 5 lower-level nodes and top 3 community nodes based on the number of edges
    top_5_nodes = nlargest(5, lower_nodes, key=lambda node: len(node.edges))
    top_3_communities = nlargest(3, communities, key=lambda node: len(node.edges))

    # Compute overall statistics in one pass
    total_num_edges = total_num_properties = 0
    document_ids = set()

    for node in all_nodes:
      total_num_edges += len(node.edges)
      total_num_properties += len(node.properties)
      for metadata in node.metadata:
        document_ids.add(metadata.document_id)

    # Fetch documents based on collected document IDs
    documents = repository.get_document(list(document_ids))

    # Total number of nodes (lower-level + community)
    total_num_nodes = len(all_nodes)

    return {
      "llm_model_type": llm_model_type,
      "documents": documents,
      "lower_nodes": lower_nodes,
      "communities": communities,
      "top_5_nodes": top_5_nodes,
      "top_3_communities": top_3_communities,
      "total_num_nodes": total_num_nodes,
      "total_num_edges": total_num_edges,
      "total_num_properties": total_num_properties,
    }

  @staticmethod
  def visualizer_print(data: dict[str, Any]) -> str:
    """Visualizes the gathered data as a dashboard.

    Args:
       data (dict[str, Any]): is a dictionry holding all the information to be printed
    returns:
       none

    """
    llm_model_type: str = data["llm_model_type"]
    documents: list[DocumentData] = data["documents"]
    top_5_nodes: list[Node] = data["top_5_nodes"]
    top_3_communities: list[Node] = data["top_3_communities"]
    total_num_nodes: int = data["total_num_nodes"]
    total_num_edges: int = data["total_num_edges"]
    total_num_properties: int = data["total_num_properties"]

    # Table for document details
    table_data = []
    for document in documents:
      table_data.append([
        document.name,
        document.chunk_num,
        document.token_num,
        document.loss_of_information
        if document.loss_of_information is not None
        else "--",
      ])

    # Output dashboard data in a readable format
    print("### Dashboard ###")
    print(f"LLM Model Type: {llm_model_type}")
    # TODO: Display embedding and reranker type when available

    # Print document table
    print("\nDocument Data:")
    print(
      tabulate(
        table_data,
        headers=["Document Name", "Chunk Num", "Tokens Num", "Information Loss"],
      )
    )

    # Print top 5 lower-level nodes
    print("\nTop 5 Lower-Level Nodes by Number of Edges:")
    for node in top_5_nodes:
      print(f"Node: {node.name}, Edges: {len(node.edges)}")

    # Print top 3 community nodes
    print("\nTop 3 Community Nodes by Number of Edges:")
    for community in top_3_communities:
      print(f"Community Node: {community.name}, Edges: {len(community.edges)}")

    # Print overall statistics
    print("\nOverall Statistics:")
    print(f"Total Number of Nodes: {total_num_nodes}")
    print(f"Total Number of Edges: {total_num_edges}")
    print(f"Total Number of Properties: {total_num_properties}")
