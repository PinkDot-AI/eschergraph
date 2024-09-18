from __future__ import annotations

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
  ) -> tuple[str, list[Chunk], list[Document], int, list[VisualDocumentElement]]:
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
    visual_elements: list[VisualDocumentElement] = [] if multi_modal else None

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
  def get_user_approval() -> bool:
    """Prompt the user for approval to build the graph.

    Returns:
        bool: True if the user approves, False otherwise.
    """
    user_input = input(
      "Press y to build graph - press anything else to cancel: "
    ).lower()
    return user_input == "y"
