from __future__ import annotations

import os
import time
from uuid import UUID
from uuid import uuid4

import tiktoken
from attrs import define
from attrs import field
from langchain_text_splitters import RecursiveCharacterTextSplitter

from eschergraph.builder.models import Chunk
from eschergraph.builder.reader.fast_pdf_parser.models import PdfParsedSegment
from eschergraph.builder.reader.fast_pdf_parser.parser import FastPdfParser
from eschergraph.builder.reader.multi_modal.data_structure import Paragraph
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.builder.reader.multi_modal.multi_modal_parser import (
  get_multi_model_elements,
)
from eschergraph.exceptions import FileTypeNotProcessableException


# TODO: add more files types: html, docx, pptx, xlsx.
@define
class Reader:
  """Reader will parse a file into chunks.

  Types accepted:
    - pdf: use a document analysis model to extract paragraphs and pagesections
    - txt: use the Langchain recursivechunker with 800 chunksize and 100 overlap
  """

  file_location: str
  multimodal: bool = False
  optimal_tokens: int = 400
  chunk_size: int = 1500
  overlap: int = 300
  total_tokens: int = 0
  chunks: list[Chunk] = field(factory=list)
  doc_id: UUID = field(factory=uuid4)
  visual_elements: list[VisualDocumentElement] = field(factory=list)
  full_text: str = ""

  @property
  def filename(self) -> str:
    """The name of the file that is being parsed."""
    return os.path.basename(self.file_location)

  def parse(self) -> list[Chunk] | None:
    """Main function that parses the document."""
    start_time = time.time()

    # Handle different file types
    if self.file_location.endswith(".txt"):
      self._parse_plain_text()

    elif self.file_location.endswith(".pdf"):
      self._parse_pdf()

    else:
      raise FileTypeNotProcessableException(
        f"File type of {self.file_location} is not processable."
      )

    self.total_tokens = sum(self._count_tokens(c.text) for c in self.chunks)
    return self.chunks

  def _parse_pdf(self) -> None:
    """Handles the parsing logic for PDF files."""
    if self.multimodal:
      parsed_paragraphs, visual_elements = get_multi_model_elements(
        file_location=self.file_location, doc_id=self.doc_id
      )
      self.visual_elements = visual_elements
      self._chunk_paragraphs(parsed_paragraphs)
    else:
      parsed_paragraphs = self._get_document_analysis()
      if parsed_paragraphs:
        self._chunk_paragraphs(parsed_paragraphs)

  def _get_document_analysis(self) -> list[Paragraph]:
    # Send the file to the specified URL and get the response
    parsed_paragraphs: list[PdfParsedSegment] = FastPdfParser.parse(
      file_path=self.file_location
    )
    reformated_paragraphs: list[Paragraph] = [
      Reader._to_paragraph_structure(pdf_segment=segment, id=idx)
      for idx, segment in enumerate(parsed_paragraphs)
    ]
    return reformated_paragraphs

  def _chunk_paragraphs(self, parsed_paragraphs: list[Paragraph]) -> None:
    current_chunk: list[str] = []
    current_token_count: int = 0
    chunk_id: int = 0

    for paragraph in parsed_paragraphs:
      if paragraph["role"] != "null":
        text: str = paragraph["content"] + "\n"
        self.full_text += text  # adding text to the full text attribute
        tokens: int = self._count_tokens(text)
        # Calculate the effective token limit
        effective_token_limit: int = self.optimal_tokens
        if current_token_count + tokens > effective_token_limit:
          self._process_text_chunk(current_chunk, chunk_id, paragraph["page_num"])
          chunk_id += 1
          current_chunk = [text]
          current_token_count = tokens
        else:
          current_chunk.append(text)
          current_token_count += tokens
        # If it's a sectionHeading and the current chunk size is greater than 80% of optimal_tokens, start a new chunk
        if (
          paragraph["role"] == "sectionHeading"
          and current_token_count > 0.7 * self.optimal_tokens
        ):
          current_chunk.pop(-1)
          self._process_text_chunk(current_chunk, chunk_id, paragraph["page_num"])
          chunk_id += 1
          current_chunk = [text]
          current_token_count = tokens
    # Process any remaining text in the last chunk
    if current_chunk:
      self._process_text_chunk(
        current_chunk, chunk_id, parsed_paragraphs[-1]["page_num"]
      )

  def _process_text_chunk(
    self, chunk_list: list[str], chunk_id: int, page_num: int | None
  ) -> None:
    """Processes a list of text chunks into a Chunk object and appends it to the chunks list if it passes the filter.

    Args:
        chunk_list (list[str]): A list of text chunks to be processed.
        chunk_id (int): An identifier for the chunk.
        page_num (int): The page number where the chunk originates.

    Returns:
        None
    """
    text: str = " ".join(chunk_list)

    if not Reader._chunk_filter(text):
      return

    self.chunks.append(
      Chunk(
        text=text.strip(),
        chunk_id=chunk_id,
        page_num=page_num,
        doc_id=self.doc_id,
      )
    )

  def _parse_plain_text(self) -> None:
    """Reads the content of a plain text file, splits it into chunks, and creates Chunk objects for each valid chunk.

    Args:
        None

    Returns:
        None
    """
    # Read the file content
    with open(self.file_location, "r", encoding="utf-8") as txt_file:
      text_content = txt_file.read().strip()
      self.full_text = text_content

    # Split the content into chunks with langchain
    text_splitter = RecursiveCharacterTextSplitter(
      chunk_size=self.chunk_size, chunk_overlap=self.overlap
    )
    all_splits = text_splitter.create_documents([text_content])

    # Filter and create Chunk objects
    self.chunks: list[Chunk] = [
      Chunk(
        text=split.page_content,
        chunk_id=idx,
        page_num=None,
        doc_id=self.doc_id,
      )
      for idx, split in enumerate(all_splits)
      if self._chunk_filter(split.page_content)
    ]

  @staticmethod
  def _chunk_filter(chunk: str) -> bool:
    """Filters out chunks based on length and non-alpha character percentage.

    Args:
        chunk (str): The text chunk to be filtered.

    Returns:
        bool: True if the chunk passes the filter, False otherwise.
    """
    min_length = 100
    if len(chunk) < min_length:
      return False
    elif Reader._contains_many_non_alpha(input_string=chunk):
      return False
    return True

  @staticmethod
  def _contains_many_non_alpha(
    input_string: str, threshold_percentage: float = 0.40
  ) -> bool:
    """Checks if a string contains more non-alpha characters than allowed based on the threshold percentage.

    Args:
        input_string (str): The string to be checked.
        threshold_percentage (float, optional): The percentage threshold for non-alpha characters (default is 0.40).

    Returns:
        bool: True if the percentage of non-alpha characters exceeds the threshold, False otherwise.
    """
    string_without_white_space = input_string.replace(" ", "")
    non_alpha_count = sum(not c.isalpha() for c in string_without_white_space)

    total_length = len(string_without_white_space)

    percentage = (non_alpha_count / total_length) if total_length > 0 else 0
    return percentage > threshold_percentage

  @staticmethod
  def _count_tokens(text: str) -> int:
    """Counts the number of tokens in a given text using a specific tokenizer.

    Args:
        text (str): The text to be tokenized.

    Returns:
        int: The number of tokens in the text.
    """
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens: list[int] = tokenizer.encode(text)
    return len(tokens)

  @staticmethod
  def _to_paragraph_structure(
    pdf_segment: PdfParsedSegment,
    id: int,
  ) -> Paragraph:
    """Converts a PDF parsed segment into a Paragraph object with appropriate role and content.

    Args:
        pdf_segment (PdfParsedSegment): The PDF segment containing type, text, and page number.
        id (int): An identifier for the paragraph.

    Returns:
        Paragraph: A Paragraph object representing the PDF segment.
    """
    role: str | None = "null"
    if pdf_segment["type"] in ["TEXT", "LIST_ITEM", "FORMULA"]:
      role = None
    elif pdf_segment["type"] == "SECTION_HEADER":
      role = "sectionHeading"

    return Paragraph(
      id=id,
      role=role,
      content=pdf_segment["text"],
      page_num=pdf_segment["page_number"],
    )
