from __future__ import annotations

from typing import TYPE_CHECKING

from eschergraph.agents.llm import ModelProvider
from eschergraph.tools.estimator import Estimator
from eschergraph.tools.reader import Chunk
from eschergraph.tools.reader import Reader

if TYPE_CHECKING:
  from eschergraph.graph.persistence.document import DocumentData


class BuildingTools:
  """This is a class for some building logic for the graph.build()."""

  @staticmethod
  def process_files(
    files: str | list[str],
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
    from eschergraph.graph.persistence.document import DocumentData

    chunks: list[Chunk] = []
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
  def get_user_approval() -> bool:
    """Prompt the user for approval to build the graph.

    Returns:
        bool: True if the user approves, False otherwise.
    """
    user_input = input(
      "Press y to build graph - press anything else to cancel: "
    ).lower()
    return user_input == "y"
