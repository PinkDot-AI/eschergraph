from __future__ import annotations

from heapq import nlargest
from typing import TYPE_CHECKING
from typing import TypedDict

from tabulate import tabulate

if TYPE_CHECKING:
  from eschergraph.graph.node import Node
  from eschergraph.graph.persistence.document import DocumentData
  from eschergraph.graph import Graph


class DashboardData(TypedDict):
  """This is the data object for dashboard."""

  llm_model_type: str
  reranker_model_type: str
  documents: list[DocumentData]
  lower_nodes: list[Node]
  communities: list[Node]
  top_5_nodes: list[Node]
  top_3_communities: list[Node]
  total_num_nodes: int
  total_num_edges: int
  total_num_properties: int


class DashboardMaker:
  """Class for generating a graph dashboard with relevant data."""

  @staticmethod
  def gather_data(graph: Graph) -> DashboardData:
    """Gathers necessary data for the dashboard.

    Args:
        graph (Graph): The graph object containing nodes and repositories.

    Returns:
        DashboardData: A dictionary containing required dashboard data.
    """
    # Get model type from the graph's model provider
    llm_model_type = graph.model.get_model_name()
    reranker_model_type = graph.reranker.get_model_name()
    # Fetch lower-level nodes and community nodes
    lower_nodes: list[Node] = graph.repository.get_all_at_level(0)
    communities: list[Node] = graph.repository.get_all_at_level(1)

    # Combine nodes for overall calculations
    all_nodes = lower_nodes + communities

    # Efficiently find the top 5 lower-level nodes and top 3 communities by edge count
    top_5_nodes = nlargest(5, lower_nodes, key=lambda node: len(node.edges))
    top_3_communities = nlargest(3, communities, key=lambda node: len(node.edges))

    # Compute total number of edges, properties, and gather document IDs
    total_num_edges = sum(len(node.edges) for node in all_nodes)
    total_num_properties = sum(len(node.properties) for node in all_nodes)
    document_ids = {
      metadata.document_id for node in all_nodes for metadata in node.metadata
    }

    # Fetch documents using the collected document IDs
    documents = graph.repository.get_documents_by_id(list(document_ids))

    # Return the gathered data
    return DashboardData(
      llm_model_type=llm_model_type,
      reranker_model_type=reranker_model_type,
      documents=documents,
      lower_nodes=lower_nodes,
      communities=communities,
      top_5_nodes=top_5_nodes,
      top_3_communities=top_3_communities,
      total_num_nodes=len(all_nodes),
      total_num_edges=total_num_edges,
      total_num_properties=total_num_properties,
    )

  @staticmethod
  def visualizer_print(data: DashboardData) -> None:
    """Prints the dashboard data in a formatted manner.

    Args:
        data (DashboardData): Dictionary containing the dashboard data.
    """
    llm_model_type: str = data["llm_model_type"]
    reranker_type: str = data["reranker_model_type"]
    documents: list[DocumentData] = data["documents"]
    top_5_nodes: list[Node] = data["top_5_nodes"]
    top_3_communities: list[Node] = data["top_3_communities"]
    total_num_nodes: int = data["total_num_nodes"]
    total_num_edges: int = data["total_num_edges"]
    total_num_properties: int = data["total_num_properties"]

    # Prepare table data for documents
    table_data = [[doc.name, doc.chunk_num, doc.token_num] for doc in documents]

    # Output dashboard data
    print("\n------------ DASHBOARD ------------")
    print(f"LLM Model Type: {llm_model_type}")
    print(f"Reranker Model Type: {reranker_type}")

    # Display document data in tabulated form
    print("\n------------ DOCUMENT DATA ------------")
    print(tabulate(table_data, headers=["Document Name", "Chunk Num", "Tokens Num"]))

    # Print top 5 lower-level nodes
    print("\n------------ TOP 5 LOWER-LEVEL NODES ------------")
    for idx, node in enumerate(top_5_nodes, 1):
      print(f"{idx}) Node: {node.name}, Edges: {len(node.edges)}")

    # Print top 3 community nodes
    print("\n------------ TOP 3 COMMUNITY NODES ------------")
    for idx, community in enumerate(top_3_communities, 1):
      print(f"{idx}) Community Node: {community.name}, Edges: {len(community.edges)}")

    # Print overall statistics
    print("\n------------ OVERALL STATISTICS ------------")
    print(f"Total Number of Nodes: {total_num_nodes}")
    print(f"Total Number of Edges: {total_num_edges}")
    print(f"Total Number of Properties: {total_num_properties}")
    print("------------ END OF DASHBOARD ------------\n")
