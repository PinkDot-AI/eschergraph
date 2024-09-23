from __future__ import annotations

from typing import Any

from eschergraph.agents.llm import ModelProvider
from eschergraph.builder.models import ProcessedFile
from eschergraph.builder.reader.reader import Reader
from eschergraph.tools.estimator import Estimator


class BuildingTools:
  """This is a class for some building logic for the graph.build()."""

  @staticmethod
  def process_files(
    files: list[str], multi_modal: bool, reader_impl: type[Reader] = Reader
  ) -> list[ProcessedFile]:
    """Process the given files and extract chunks, document data, and total tokens.

    Args:
      files (list[str]): A list of file paths to process.
      multi_modal (bool): A flag indicating whether the parsing should be multi-modal.
      reader_impl (type[Reader]): The reader class to use, added only for testing.

    Returns:
      A list of processed files.
    """
    from eschergraph.persistence.document import Document

    processed_files: list[ProcessedFile] = []

    for file in files:
      reader = reader_impl(file_location=file, multimodal=multi_modal)
      reader.parse()

      processed_files.append(
        ProcessedFile(
          document=Document(
            id=reader.doc_id,
            name=reader.filename,
            chunk_num=len(reader.chunks),
            token_num=reader.total_tokens,
          ),
          full_text=reader.full_text,
          chunks=reader.chunks,
          visual_elements=reader.visual_elements if multi_modal else None,
        )
      )

    return processed_files

  @staticmethod
  def display_build_info(
    processed_files: list[ProcessedFile], model: ModelProvider
  ) -> None:
    """Display information about the graph building process.

    Args:
      processed_files (list[ProcessedFile]): A list of processed files.
      model (Model): The model to be used for analysis.
    """
    num_chunks: int = sum(len(file.chunks) for file in processed_files)
    total_tokens: int = sum(file.document.token_num for file in processed_files)
    model_name = model.get_model_name()
    estimated_time = Estimator.get_time_indication(
      num_chunks=num_chunks, model=model_name
    )
    estimated_cost = Estimator.get_cost_indication(
      total_tokens=total_tokens, model=model_name
    )
    print("------------------------INFO-------------------------")
    print(
      f"This will parse {num_chunks} chunks, analyze {total_tokens} tokens\n"
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
