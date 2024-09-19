from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from eschergraph.agents.llm import ModelProvider
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.builder.reader.reader import Chunk
from eschergraph.builder.reader.reader import Reader
from eschergraph.tools.estimator import Estimator

if TYPE_CHECKING:
  from eschergraph.persistence.document import Document


class BuildingTools:
  """This is a class for some building logic for the graph.build()."""

  @staticmethod
  def process_files(
    files: list[str], multi_modal: bool
  ) -> tuple[str, list[Chunk], list[Document], int, list[VisualDocumentElement] | None]:
    """Process the given files and extract chunks, document data, and total tokens.

    Args:
      files (list[str]): A list of file paths to process.
      multi_modal (bool): A flag indicating whether the parsing should be multi-modal.

    Returns:
      tuple: A tuple containing the following:
        - str: The concatenated text of all documents.
        - list[Chunk]: A list of Chunk objects extracted from the documents.
        - list[Document]: A list of Document objects representing metadata for each document.
        - int: The total number of tokens processed across all documents.
        - list[VisualDocumentElement]: A list of visual elements (only if `multi_modal` is True).
    """
    from eschergraph.persistence.document import Document

    chunks: list[Chunk] = []
    document_data: list[Document] = []
    total_tokens: int = 0
    full_text: str = ""
    visual_elements: list[VisualDocumentElement] = []

    for file in files:
      reader = Reader(file_location=file, multimodal=multi_modal)
      reader.parse()
      chunks.extend(reader.chunks)
      full_text += reader.full_text + "\n"

      if multi_modal:
        visual_elements.extend(reader.visual_elements)

      doc_data = Document(
        id=reader.doc_id,
        name=reader.filename,
        chunk_num=len(reader.chunks),
        token_num=reader.total_tokens,
      )
      document_data.append(doc_data)
      total_tokens += reader.total_tokens

    return full_text, chunks, document_data, total_tokens, visual_elements

  @staticmethod
  def display_build_info(
    chunks: list[Chunk], total_tokens: int, model: ModelProvider
  ) -> None:
    """Display information about the graph building process.

    Args:
        chunks (list[Chunk]): The list of chunks to be processed.
        total_tokens (int): The total number of tokens to be processed.
        model (Model): The model to be used for analysis.
    """
    model_name = model.get_model_name()
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
  def check_node_ext(input_dict: dict[str, Any]) -> bool:
    """Checks if the input_dict matches the NodeExt structure."""
    required_keys = {"name": str, "description": str}
    return all(
      key in input_dict and isinstance(input_dict[key], required_type)
      for key, required_type in required_keys.items()
    )

  @staticmethod
  def check_edge_ext(input_dict: dict[str, Any]) -> bool:
    """Checks if the input_dict matches the EdgeExt structure."""
    required_keys = {"source": str, "target": str, "relationship": str}
    return all(
      key in input_dict and isinstance(input_dict[key], required_type)
      for key, required_type in required_keys.items()
    )

  @staticmethod
  def check_property_ext(input_dict: dict[str, Any]) -> bool:
    """Checks if the input_dict matches the PropertyExt structure."""
    required_keys = {"entity_name": str, "properties": list}
    return all(
      key in input_dict and isinstance(input_dict[key], required_type)
      for key, required_type in required_keys.items()
    ) and all(isinstance(prop, str) for prop in input_dict["properties"])

  @staticmethod
  def check_node_edge_ext(input_dict: dict[str, Any]) -> bool:
    """Checks if the input_dict matches the NodeEdgeExt structure."""
    required_keys = {"entities": list, "relationships": list}

    if not all(
      key in input_dict and isinstance(input_dict[key], list) for key in required_keys
    ):
      return False

    # Check each entity and relationship inside the lists
    return all(
      BuildingTools.check_node_ext(entity) for entity in input_dict["entities"]
    ) and all(
      BuildingTools.check_edge_ext(relationship)
      for relationship in input_dict["relationships"]
    )
