from __future__ import annotations

import os
from typing import Optional
from uuid import UUID

import fitz  # PyMuPDF
import requests
from PIL import Image

from eschergraph.builder.reader.multi_modal.data_structure import AnalysisResult
from eschergraph.builder.reader.multi_modal.data_structure import BoundingRegion
from eschergraph.builder.reader.multi_modal.data_structure import Paragraph
from eschergraph.builder.reader.multi_modal.data_structure import Table
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.exceptions import ExternalProviderException


def get_multi_model_elements(
  file_location: str, doc_id: UUID
) -> tuple[list[Paragraph], list[VisualDocumentElement]]:
  """Retrieves multi-modal elements from a file location by parsing the document.

  Args:
      file_location (str): The path to the document file.
      doc_id (UUID): The document ID.

  Returns:
      list[VisualDocumentElement]: A list of visual elements extracted from the document.
  """
  try:
    results: AnalysisResult | None = _get_pinkdot_parser(document_path=file_location)
    if results:
      visual_elements: list[VisualDocumentElement] = _handle_multi_modal(
        results, file_location, doc_id
      )
      parsed_paragraphs: list[Paragraph] = results["paragraphs"]
      return parsed_paragraphs, visual_elements
    else:
      raise ExternalProviderException("Pinkdot AI platform did not return valid object")
  except Exception as e:
    raise e


def _handle_multi_modal(
  analysis_results: AnalysisResult, file_location: str, doc_id: UUID
) -> list[VisualDocumentElement]:
  """Processes and saves tables and figures from analysis results.

  Args:
      analysis_results (AnalysisResult): The analysis results containing tables, figures, and paragraphs.
      file_location (str): The file location of the document.
      doc_id (UUID): The document ID.

  Returns:
      list[VisualDocumentElement]: A list of visual elements representing tables and figures.
  """
  base_name = os.path.basename(file_location)
  output_folder = os.path.join("eschergraph_storage", base_name)

  # Create subfolders for tables and figures
  tables_folder = os.path.join(output_folder, "tables")
  figures_folder = os.path.join(output_folder, "figures")
  os.makedirs(tables_folder, exist_ok=True)
  os.makedirs(figures_folder, exist_ok=True)

  # Process tables and figures
  visual_elements: list[VisualDocumentElement] = []
  visual_elements.extend(
    _handle_tables(analysis_results, tables_folder, doc_id, file_location)
  )
  visual_elements.extend(
    _handle_figures(analysis_results, figures_folder, doc_id, file_location)
  )

  return visual_elements


def _handle_tables(
  analysis_results: AnalysisResult, tables_folder: str, doc_id: UUID, file_location: str
) -> list[VisualDocumentElement]:
  """Processes and saves tables from analysis results.

  Args:
      analysis_results (AnalysisResult): The analysis results containing tables.
      tables_folder (str): The folder to save the tables.
      doc_id (UUID): The document ID.
      file_location (str): The file location of the document.

  Returns:
      list: List of VisualDocumentElement for tables.
  """
  visual_elements = []
  for table_idx, table in enumerate(analysis_results["tables"]):
    caption = table["caption"]
    markdown_output = f"{caption}\n"
    markdown_output += _generate_markdown_table(table)

    for region in table["bounding_regions"]:
      cropped_image_filename: str = _save_cropped_image(
        file_location, region, tables_folder, table_idx, "TABLE"
      )
      v = VisualDocumentElement(
        content=markdown_output,
        caption=caption,
        save_location=cropped_image_filename,
        doc_id=doc_id,
        page_num=table["page_num"],
        type="TABLE",
      )
      visual_elements.append(v)
  return visual_elements


def _handle_figures(
  analysis_results: AnalysisResult,
  figures_folder: str,
  doc_id: UUID,
  file_location: str,
) -> list[VisualDocumentElement]:
  """Processes and saves figures from analysis results.

  Args:
      analysis_results (AnalysisResult): The analysis results containing figures.
      figures_folder (str): The folder to save the figures.
      doc_id (UUID): The document ID.
      file_location (str): The file location of the document.

  Returns:
      list: List of VisualDocumentElement for figures.
  """
  visual_elements: list[VisualDocumentElement] = []
  for figure_idx, figure in enumerate(analysis_results["figures"]):
    caption = figure["caption"]

    for region in figure["bounding_regions"]:
      cropped_image_filename = _save_cropped_image(
        file_location, region, figures_folder, figure_idx, "FIGURE"
      )
      v = VisualDocumentElement(
        content="",
        caption=caption,
        save_location=cropped_image_filename,
        doc_id=doc_id,
        page_num=figure["page_num"],
        type="FIGURE",
      )
      visual_elements.append(v)
  return visual_elements


def _get_bounding_box(region: BoundingRegion) -> Optional[list[float]]:
  """Returns the bounding box of a region if the polygon is available, otherwise None."""
  polygon = region["polygon"]
  if polygon is None or len(polygon) < 6:
    # Return None or raise an exception if polygon is None or has insufficient points
    return None

  bounding_box = [
    polygon[0],  # x0 (left)
    polygon[1],  # y0 (top)
    polygon[4],  # x1 (right)
    polygon[5],  # y1 (bottom)
  ]
  return bounding_box


def _save_cropped_image(
  file_location: str, region: BoundingRegion, folder: str, idx: int, element_type: str
) -> str:
  """Crops an image from a PDF page and saves it.

  Args:
      file_location (str): The location of the PDF file.
      region (dict): The bounding region of the element.
      folder (str): The folder to save the image in.
      idx (int): The index of the element (table or figure).
      element_type (str): The type of the element (TABLE or FIGURE).

  Returns:
      str: The file path of the saved image.
  """
  boundingbox = _get_bounding_box(region=region)
  if boundingbox:
    cropped_image = _crop_image_from_pdf_page(
      file_location, region["page_number"] - 1, boundingbox
    )
    output_file = f"{element_type.lower()}_{idx}.png"
    cropped_image_filename = os.path.join(folder, output_file)
    cropped_image.save(cropped_image_filename)
    return cropped_image_filename
  else:
    return ""


def _generate_markdown_table(table: Table) -> str:
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


def _get_pinkdot_parser(
  document_path: str, endpoint_url: str = "http://127.0.0.1:8000/analyze_document"
) -> None | AnalysisResult:
  """Sends a PDF document to an API endpoint for analysis and returns the parsed analysis results.

  Args:
    document_path (str): The file path of the PDF document to be analyzed.
    endpoint_url (str, optional): The URL of the API endpoint. Defaults to "http://127.0.0.1:8000/analyze_document".

  Returns:
    None or list[AnalysisResult]: A list of `AnalysisResult` objects if the analysis is successful, or None if no results are available.
  """
  if not os.path.isfile(document_path):
    raise FileNotFoundError(f"The file at {document_path} does not exist.")

  with open(document_path, "rb") as file:
    files = {"file": (os.path.basename(document_path), file, "application/pdf")}
    try:
      response = requests.post(endpoint_url, files=files)
      response.raise_for_status()  # Check if the request was successful
    except requests.RequestException as e:
      raise Exception(f"Error while calling API: {str(e)}")

    try:
      # Parse the JSON response
      data = response.json()
      # Validate and parse the response into the AnalysisResult model
      analysis_result: AnalysisResult = AnalysisResult(
        tables=data["tables"], figures=data["figures"], paragraphs=data["paragraphs"]
      )  # ignore
      return analysis_result
    except Exception as e:
      raise ValueError(f"Error parsing the response: {str(e)}")


def _crop_image_from_pdf_page(
  pdf_path: str, page_number: int, bounding_box: list[float]
) -> Image.Image:
  """Crop a region from a given page in a PDF and handle cases where the bounding box is outside the page.

  Args:
    pdf_path (str): The path to the PDF file.
    page_number (int): The page number to crop from (0-indexed).
    bounding_box (tuple): The bounding box coordinates in the format (x0, y0, x1, y1).

  Returns:
    A PIL Image of the cropped area.
  """
  # Load the PDF and the page
  doc = fitz.open(pdf_path)
  page = doc.load_page(page_number)

  # Get page dimensions in points (72 points = 1 inch)
  page_width, page_height = page.rect.width, page.rect.height

  # Ensure bounding box coordinates are ordered correctly
  x0, y0, x1, y1 = bounding_box
  if y0 > y1:
    y0, y1 = y1, y0  # Swap values if y0 is greater than y1
  if x0 > x1:
    x0, x1 = x1, x0  # Swap values if x0 is greater than x1

  # Limit bounding box to the page dimensions
  x0 = max(0, min(x0, page_width))
  y0 = max(0, min(y0, page_height))
  x1 = max(0, min(x1, page_width))
  y1 = max(0, min(y1, page_height))

  # Convert to pixel coordinates (assuming 72 DPI for points)
  crop_box = [x * 72 for x in (x0, y0, x1, y1)]

  # Cropping the page. The rect requires the coordinates in the format (x0, y0, x1, y1).
  rect = fitz.Rect(crop_box)
  pix_cropped = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), clip=rect)

  # Create an image from the pixmap
  size: tuple[int, int] = pix_cropped.width, pix_cropped.height  # ignore
  img_cropped = Image.frombytes(mode="RGB", size=size, data=pix_cropped.samples)

  doc.close()

  return img_cropped
