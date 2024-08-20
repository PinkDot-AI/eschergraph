from __future__ import annotations

import os
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

import requests
import tiktoken
from attrs import define
from attrs import field
from langchain_text_splitters import RecursiveCharacterTextSplitter

from eschergraph.exceptions import ExternalProviderException
from eschergraph.exceptions import FileTypeNotProcessableException


@define
class Chunk:
  """Datastructure of the chunk objects."""

  text: str
  chunk_id: int
  doc_id: UUID
  page_num: Optional[int]
  doc_name: str


@define
class Reader:
  """This class will turn a file location into chunk objects as defined above.

  Types accepted:
  pdf, txt

  PDF files: use a document analysis model to extract paragraphs and pagesections
  Txt files: use the Langchain recursivechunker with 800 chunksize and 100 overlap.
  TODO add more files types: html, docx, pptx, xlsx.

  """

  file_location: str
  multimodal: bool
  optimal_tokens: int = 400
  chunk_size: int = 1500
  overlap: int = 300
  total_tokens: int = 0
  all_chunks: List[Chunk] = field(factory=list)
  doc_id: UUID = field(factory=uuid4)
  filename: str = field(init=False)

  def __attrs_post_init__(self) -> None:
    """Post-initialization to set derived attributes."""
    self.filename = os.path.basename(self.file_location)

  def _get_document_analysis(self) -> Optional[Any]:
    # Send the file to the specified URL and get the response
    with open(self.file_location, "rb") as file:
      files = {"file": file}
      response = requests.post("http://localhost:5060/document-analysis", files=files)
    # Check if the response is in JSON format and process it
    try:
      return response.json()
    except Exception as e:
      raise ExternalProviderException from e

  def _handle_json_response(self, response_json: List[Dict[str, Any]]) -> List[Chunk]:
    current_chunk: List[str] = []
    current_token_count: int = 0
    chunk_id: int = 0  # Initialize a chunk ID counter

    for i, item in enumerate(response_json):
      if item["type"] in ["TABLE", "PICTURE", "CAPTION"] and self.multimodal:
        #### TO DO: implement multimodal handling
        pass

      elif item["type"] in ["TEXT", "SECTION_HEADER", "LIST_ITEM", "FORMULA"]:
        text: str = item["text"] + "\n"
        tokens: int = self._count_tokens(text)
        # Calculate the effective token limit
        effective_token_limit: int = self.optimal_tokens
        if (
          item["type"] == "LIST_ITEM"
          and i + 1 < len(response_json)
          and response_json[i + 1]["type"] == "LIST_ITEM"
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
    return self.all_chunks

  @staticmethod
  def _count_tokens(text: str) -> int:
    # Assuming you have installed the tiktoken library and configured the tokenizer
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens: List[str] = tokenizer.encode(text)
    return len(tokens)

  def _process_text_chunk(
    self, chunk_list: List[str], chunk_id: int, page_num: int
  ) -> None:
    # Add your logic to handle text chunks
    text: str = " ".join(chunk_list)
    if not self._chunk_filter(text):
      return
    chunk: Chunk = Chunk(
      text=text,
      chunk_id=chunk_id,
      page_num=page_num,
      doc_id=self.doc_id,
      doc_name=self.file_location,
    )
    self.all_chunks.append(chunk)

  def _handle_plain_text(self) -> None:
    with open(self.file_location, "r", encoding="utf-8") as txt_file:
      text_content: str = (
        txt_file.read().strip()
      )  # Reads the entire file content as a single string
    text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
      chunk_size=self.chunk_size, chunk_overlap=self.overlap
    )
    all_splits = text_splitter.create_documents([text_content])
    chunks: List[Chunk] = []
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
    self.all_chunks = chunks

  def parse(self) -> List[Chunk] | None:
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

    total_tokens: int = sum(self._count_tokens(c.text) for c in self.all_chunks)
    self.total_tokens = total_tokens
    print(
      f"Parsed {self.file_location} with multimodal = {self.multimodal} into {len(self.all_chunks)} chunks, {self.total_tokens} tokens, in {round(time.time() - start_time, 3)} seconds"
    )
    return self.all_chunks

  def _chunk_filter(self, chunk: str) -> bool:
    min_length = 100
    if len(chunk) < min_length:
      return False
    elif self._contains_many_non_alpha(input_string=chunk):
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
