from __future__ import annotations

import mimetypes

import fitz  # PyMuPDF
from PIL import Image


def crop_image_from_image(image_path, page_number, bounding_box) -> Image:
  """Crop an image from a file.

  Args:
      image_path (str): The path to the image file.
      page_number (int): The page number of the image to crop (for TIFF format, 0-indexed).
      bounding_box (tuple): The bounding box coordinates in the format (left, upper, right, lower).

  Returns:
      A PIL Image of the cropped area.
  """
  with Image.open(image_path) as img:
    if img.format == "TIFF":
      # Open the TIFF image
      img.seek(page_number)
      img = img.copy()

    # The bounding box is expected to be in the format (left, upper, right, lower).
    cropped_image = img.crop(bounding_box)
    return cropped_image


def crop_image_from_pdf_page(pdf_path, page_number, bounding_box) -> Image:
  """Crop a region from a given page in a PDF.

  Args:
      pdf_path (str): The path to the PDF file.
      page_number (int): The page number to crop from (0-indexed).
      bounding_box (tuple): The bounding box coordinates in the format (x0, y0, x1, y1).

  Returns:
      A PIL Image of the cropped area.
  """
  doc = fitz.open(pdf_path)
  page = doc.load_page(page_number)

  # Cropping the page. The rect requires the coordinates in the format (x0, y0, x1, y1).
  bbx = [x * 72 for x in bounding_box]
  rect = fitz.Rect(bbx)
  pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), clip=rect)

  img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

  doc.close()

  return img


def crop_image_from_file(file_path, page_number, bounding_box) -> Image:
  """Crop an image from a file.

  Args:
      file_path (str): The path to the file.
      page_number (int): The page number (for PDF and TIFF files, 0-indexed).
      bounding_box (tuple): The bounding box coordinates in the format (x0, y0, x1, y1).

  Returns:
      A PIL Image of the cropped area.
  """
  mime_type = mimetypes.guess_type(file_path)[0]

  if mime_type == "application/pdf":
    return crop_image_from_pdf_page(file_path, page_number, bounding_box)
  else:
    return crop_image_from_image(file_path, page_number, bounding_box)
