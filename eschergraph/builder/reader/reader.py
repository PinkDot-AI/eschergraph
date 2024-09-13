from __future__ import annotations

import base64
import io
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
from PIL import Image

from eschergraph.builder.reader.crop_images import crop_image_from_file
from eschergraph.builder.reader.fast_pdf_parser import FastPdfParser
from eschergraph.builder.reader.fast_pdf_parser import PdfParsedSegment
from eschergraph.builder.reader.pdf_parser_large.data_structure import (
  AnalysisResult,
)
from eschergraph.builder.reader.pdf_parser_large.data_structure import (
  Table,
)
from eschergraph.builder.reader.pdf_parser_large.pdf_parser_large import (
  pdf_parser_large,
)
from eschergraph.exceptions import FileTypeNotProcessableException


@define
class Chunk:
  """The chunk object."""

  text: str
  chunk_id: int
  doc_id: UUID
  page_num: Optional[int]
  doc_name: str


@define
class VisualDocumentElement:
  """This is the dataclasse for the Visual elemenets in a document. For now Figures and Tables."""

  content: str
  caption: str | None
  save_location: str
  page_num: int | None
  doc_id: UUID
  doc_name: str
  type: str


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
      if self.multimodal:
        results = self._get_document_analysis_large()
        if results:
          self._handle_multi_modal(results)
      else:
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

  def _get_document_analysis_large(self) -> list[PdfParsedSegment]:
    return pdf_parser_large(document_path=self.file_location)

  def save_image_from_base64(self, base64_string: str, output_path: str) -> None:
    """Decodes a base64 string and saves the resulting image to the specified path.

    Args:
        base64_string (str): The base64-encoded image string.
        output_path (str): The file path where the image will be saved.

    Returns:
        None

    Raises:
        Exception: If there's an error during image processing or saving.
    """
    try:
      # Decode the base64 string to bytes
      image_bytes = base64.b64decode(base64_string)

      # Create a BytesIO object from the image bytes
      image_buffer = io.BytesIO(image_bytes)

      # Open the image using Pillow
      with Image.open(image_buffer) as img:
        # Save the image in its original format with maximum quality
        img.save(output_path, quality=95, subsampling=0)

    except Exception as e:
      print(f"Error saving image: {str(e)}")

  def _handle_multi_modal(self, analysis_results: AnalysisResult) -> None:
    """Processes and saves tables and figures from analysis results, creating markdown for tables and.

    saving cropped images for both tables and figures.

    Args:
      analysis_results (AnalysisResult): The analysis results containing tables, figures, and paragraphs.

    Returns:
        None
    """
    base_name = os.path.basename(self.file_location)
    output_folder = os.path.join("eschergraph_storage", base_name)

    # Create subfolders for tables and figures
    tables_folder = os.path.join(output_folder, "tables")
    figures_folder = os.path.join(output_folder, "figures")
    os.makedirs(tables_folder, exist_ok=True)
    os.makedirs(figures_folder, exist_ok=True)

    # Handling tables
    for table_idx, table in enumerate(analysis_results["tables"]):
      caption = table["caption"]
      markdown_output = f"### Table {table_idx + 1}: {table['caption']}\n\n"
      markdown_output += self.generate_markdown_table(table)
      for region in table["bounding_regions"]:
        if table["bounding_regions"]:
          boundingbox = (
            region["polygon"][0],  # x0 (left)
            region["polygon"][1],  # y0 (top)
            region["polygon"][4],  # x1 (right)
            region["polygon"][5],  # y1 (bottom)
          )
        cropped_image = crop_image_from_file(
          self.file_location, region["page_number"] - 1, boundingbox
        )
        output_file = f"table_{table_idx}.png"
        cropped_image_filename = os.path.join(tables_folder, output_file)
        cropped_image.save(cropped_image_filename)
        v = VisualDocumentElement(
          content=markdown_output,
          caption=caption,
          save_location=cropped_image_filename,
          doc_id=self.doc_id,
          doc_name=self.filename,
          page_num=table["page_num"],
          type="TABLE",
        )
        self.visual_elements.append(v)
    # Handling figures
    for figure_idx, figure in enumerate(analysis_results["figures"]):
      caption = figure["caption"]

      figure_filename = f"figure_{figure_idx + 1}.png"
      figure_path = os.path.join(figures_folder, figure_filename)

      self.save_image_from_base64(figure["content"], figure_path)

      # Create a VisualDocumentElement for the figure
      v = VisualDocumentElement(
        content=markdown_output,
        caption=caption,
        save_location=figure_path,
        doc_id=self.doc_id,
        doc_name=self.filename,
        page_num=figure["page_num"],
        type="FIGURE",
      )
      self.visual_elements.append(v)

  def generate_markdown_table(self, table: Table) -> str:
    """Generates a markdown representation of a table from the given Table data.

    Args:
        table (Table): The table data containing cells, row and column count.

    Returns:
        str: A string containing the table formatted as markdown.

    """
    # Initialize a 2D list (rows x columns) for the table content
    markdown_table = [
      ["" for _ in range(table["column_count"])] for _ in range(table["row_count"])
    ]

    # Populate the 2D list with content from the table cells
    for cell in table["cells"]:
      markdown_table[cell["row_index"]][cell["column_index"]] = cell["content"]

    # Convert the 2D list to markdown format
    markdown_str = ""

    # Add the header row (first row)
    header_row = markdown_table[0]
    markdown_str += "| " + " | ".join(header_row) + " |\n"

    # Add the separator (markdown requires a line with dashes between header and content)
    markdown_str += "| " + " | ".join(["---"] * table["column_count"]) + " |\n"

    # Add the remaining rows
    for row in markdown_table[1:]:
      markdown_str += "| " + " | ".join(row) + " |\n"

    return markdown_str

  def _handle_json_response(self, response_json: Any) -> None:
    current_chunk: list[str] = []
    current_token_count: int = 0
    chunk_id: int = 0

    for i, item in enumerate(response_json):
      if item["type"] in ["TEXT", "SECTION_HEADER", "list_ITEM", "FORMULA"]:
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
