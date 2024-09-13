from __future__ import annotations

import fitz  # PyMuPDF
from PIL import Image


def crop_image_from_pdf_page(pdf_path, page_number, bounding_box) -> Image:
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
  img_cropped = Image.frombytes(
    "RGB", [pix_cropped.width, pix_cropped.height], pix_cropped.samples
  )

  doc.close()

  return img_cropped
