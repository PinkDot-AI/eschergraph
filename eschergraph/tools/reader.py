from __future__ import annotations

import os
import time
from typing import Any
from typing import Optional
from uuid import UUID
from uuid import uuid4

import tiktoken
from attrs import define
from attrs import field
from langchain_text_splitters import RecursiveCharacterTextSplitter

from eschergraph.exceptions import FileTypeNotProcessableException
from eschergraph.tools.fast_pdf_parser import FastPdfParser
from eschergraph.tools.fast_pdf_parser import PdfParsedSegment


@define
class Chunk:
  """The chunk object."""

  text: str
  chunk_id: int
  doc_id: UUID
  page_num: Optional[int]
  doc_name: str


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

  @property
  def filename(self) -> str:
    """The name of the file that is being parsed."""
    return os.path.basename(self.file_location)

  def parse(self) -> list[Chunk] | None:
    """This is the main function that parses the document."""
    start_time: float = time.time()
    if self.file_location.endswith(".txt"):
      # Handle txt file
      self._handle_plain_text()
    elif self.file_location.endswith(".pdf"):
      # Handle pdf file
      response_json = self._get_document_analysis()
      if response_json:
        self._handle_json_response(response_json)
    else:
      # Raise an exception for unsupported file types
      raise FileTypeNotProcessableException(
        f"File type of {self.file_location} is not processable."
      )

    total_tokens: int = sum(self._count_tokens(c.text) for c in self.chunks)
    self.total_tokens = total_tokens
    print(
      f"Parsed {self.file_location} with multimodal = {self.multimodal} into {len(self.chunks)} chunks, {self.total_tokens} tokens, in {round(time.time() - start_time, 3)} seconds"
    )
    return self.chunks

  def _get_document_analysis(self) -> list[PdfParsedSegment]:
    # Send the file to the specified URL and get the response
    return FastPdfParser.parse(file_path=self.file_location)

  def _handle_json_response(self, response_json: Any) -> None:
    current_chunk: list[str] = []
    current_token_count: int = 0
    chunk_id: int = 0

    for i, item in enumerate(response_json):
      if item["type"] in ["TABLE", "PICTURE", "CAPTION"] and self.multimodal:
        # TODO: implement multimodal handling
        pass

      elif item["type"] in ["TEXT", "SECTION_HEADER", "list_ITEM", "FORMULA"]:
        text: str = item["text"] + "\n"
        tokens: int = self._count_tokens(text)
        # Calculate the effective token limit
        effective_token_limit: int = self.optimal_tokens
        if (
          item["type"] == "list_ITEM"
          and i + 1 < len(response_json)
          and response_json[i + 1]["type"] == "list_ITEM"
        ):
          effective_token_limit = int(self.optimal_tokens * 1.2)
        # Check if adding this item exceeds the effective token limit
        if current_token_count + tokens > effective_token_limit:
          # Process the current chunk and start a new one with the current item
          self._process_text_chunk(current_chunk, chunk_id, int(item["page_number"]))
          chunk_id += 1  # Increment the chunk ID
          current_chunk = [text]
          current_token_count = tokens
        else:
          # Add the item to the current chunk
          current_chunk.append(text)
          current_token_count += tokens
        # If it's a SECTION_HEADER and the current chunk size is greater than 80% of optimal_tokens, start a new chunk
        if (
          item["type"] == "SECTION_HEADER"
          and current_token_count > 0.8 * self.optimal_tokens
        ):
          current_chunk.pop(-1)
          self._process_text_chunk(current_chunk, chunk_id, int(item["page_number"]))
          chunk_id += 1  # Increment the chunk ID
          current_chunk = [text]
          current_token_count = tokens
    # Process any remaining text in the last chunk
    if current_chunk:
      self._process_text_chunk(
        current_chunk, chunk_id, int(response_json[-1]["page_number"])
      )

  @staticmethod
  def _count_tokens(text: str) -> int:
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens: list[int] = tokenizer.encode(text)
    return len(tokens)

  def _process_text_chunk(
    self, chunk_list: list[str], chunk_id: int, page_num: int
  ) -> None:
    text: str = " ".join(chunk_list)

    if not Reader._chunk_filter(text):
      return

    chunk: Chunk = Chunk(
      text=text,
      chunk_id=chunk_id,
      page_num=page_num,
      doc_id=self.doc_id,
      doc_name=self.file_location,
    )
    self.chunks.append(chunk)

  def _handle_plain_text(self) -> None:
    with open(self.file_location, "r", encoding="utf-8") as txt_file:
      text_content: str = (
        txt_file.read().strip()
      )  # Reads the entire file content as a single string
    text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
      chunk_size=self.chunk_size, chunk_overlap=self.overlap
    )
    all_splits = text_splitter.create_documents([text_content])
    chunks: list[Chunk] = []
    for idx, split in enumerate(all_splits):
      chunk_text: str = split.page_content
      if self._chunk_filter(chunk_text):
        chunks.append(
          Chunk(
            text=chunk_text,
            chunk_id=idx,
            page_num=None,
            doc_id=self.doc_id,
            doc_name=self.filename,
          )
        )
    self.chunks = chunks

  @staticmethod
  def _chunk_filter(chunk: str) -> bool:
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
    # This function checks where there are too many non-alpha characters in the chunk. This is a good indication of bad chunks.
    # Sometimes chunks with a lot of math do get removed with this filter, so that's why I chose a 0.4 threshold (quite high).
    # The threshold_percentage can be quite sensitive to the test.
    # threshold_percentage means the percentage of non-alpha characters allowed in the string, NOT including whitespaces
    string_without_white_space = input_string.replace(" ", "")
    non_alpha_count = sum(not c.isalpha() for c in string_without_white_space)

    total_length = len(string_without_white_space)

    percentage = (non_alpha_count / total_length) if total_length > 0 else 0
    # Return True if the percentage exceeds the threshold
    return percentage > threshold_percentage
