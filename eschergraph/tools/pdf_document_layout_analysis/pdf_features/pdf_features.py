from __future__ import annotations

import os
import subprocess
import tempfile
from os.path import exists
from os.path import join
from pathlib import Path

from lxml import etree
from lxml.etree import ElementBase
from lxml.etree import XMLSyntaxError
from pypdf import PdfReader
from pypdf import PdfWriter

from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_font import PdfFont
from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_modes import (
  PdfModes,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_page import PdfPage
from eschergraph.tools.pdf_document_layout_analysis.pdf_token_type_labels.pdf_labels import (
  PdfLabels,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_token_type_labels.token_type import (
  TokenType,
)

"""
Slightly altered code that has been copied from https://github.com/huridocs/pdf-document-layout-analysis.

Altered the check for whether a pdf is encrypted, and the decryption of a pdf to remove the external
dependency qpdf.
"""


class PdfFeatures:
  def __init__(
    self,
    pages: list[PdfPage],
    fonts: list[PdfFont],
    file_name="",
    file_type: str = "",
  ):
    self.pages = pages
    self.fonts = fonts
    self.file_name = file_name
    self.file_type = file_type
    self.pdf_modes: PdfModes = PdfModes()

  def loop_tokens(self):
    for page in self.pages:
      for token in page.tokens:
        yield page, token

  def set_token_types(self, labels: PdfLabels):
    if not labels.pages:
      return

    for page, token in self.loop_tokens():
      token.token_type = TokenType.from_index(
        labels.get_label_type(token.page_number, token.bounding_box)
      )

  @staticmethod
  def from_poppler_etree(
    file_path: str | Path, file_name: str | None = None, dataset: str | None = None
  ):
    try:
      file_content: str = open(file_path, errors="ignore").read()
    except (FileNotFoundError, UnicodeDecodeError, XMLSyntaxError):
      return None

    return PdfFeatures.from_poppler_etree_content(
      file_path, file_content, file_name, dataset
    )

  @staticmethod
  def from_poppler_etree_content(
    file_path: str | Path,
    file_content: str,
    file_name: str | None = None,
    dataset: str | None = None,
  ):
    if not file_content:
      return PdfFeatures.get_empty()

    file_bytes: bytes = file_content.encode("utf-8")

    parser = etree.XMLParser(recover=True, encoding="utf-8")
    root: ElementBase = etree.fromstring(file_bytes, parser=parser)

    if root is None or not len(root):
      return PdfFeatures.get_empty()

    fonts: list[PdfFont] = [
      PdfFont.from_poppler_etree(style_tag) for style_tag in root.findall(".//fontspec")
    ]
    fonts_by_font_id: dict[str, PdfFont] = {font.font_id: font for font in fonts}
    tree_pages: list[ElementBase] = [tree_page for tree_page in root.findall(".//page")]
    pages: list[PdfPage] = [
      PdfPage.from_poppler_etree(tree_page, fonts_by_font_id, file_name)
      for tree_page in tree_pages
    ]

    file_type: str = file_path.split("/")[-2] if not dataset else dataset
    file_name: str = Path(file_path).name if not file_name else file_name

    return PdfFeatures(pages, fonts, file_name, file_type)

  @staticmethod
  def contains_text(xml_path: str):
    try:
      file_content = open(xml_path).read()
      file_bytes = file_content.encode("utf-8")
      root: ElementBase = etree.fromstring(file_bytes)
      text_elements: list[ElementBase] = root.findall(".//text")
    except (FileNotFoundError, UnicodeDecodeError, XMLSyntaxError):
      return False
    return len(text_elements) > 0

  @staticmethod
  def is_pdf_encrypted(pdf_path):
    with open(pdf_path, "rb") as file:
      reader = PdfReader(file)
      return reader.is_encrypted

  @staticmethod
  def decrypt_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # We can only decrypt if the password is empty
    reader.decrypt("")

    # Add all pages to the writer
    for page in reader.pages:
      writer.add_page(page)

    # Save the new PDF to a file
    with open(pdf_path, "wb") as f:
      writer.write(f)

  @staticmethod
  def from_pdf_path(pdf_path, xml_path: str = None):
    remove_xml = False if xml_path else True
    xml_path = xml_path if xml_path else join(tempfile.gettempdir(), "pdf_etree.xml")

    if PdfFeatures.is_pdf_encrypted(pdf_path):
      PdfFeatures.decrypt_pdf()

    subprocess.run(["pdftohtml", "-i", "-xml", "-zoom", "1.0", pdf_path, xml_path])

    if not PdfFeatures.contains_text(xml_path):
      subprocess.run([
        "pdftohtml",
        "-i",
        "-hidden",
        "-xml",
        "-zoom",
        "1.0",
        pdf_path,
        xml_path,
      ])

    pdf_features = PdfFeatures.from_poppler_etree(
      xml_path, file_name=Path(pdf_path).name
    )

    if remove_xml and exists(xml_path):
      os.remove(xml_path)

    return pdf_features

  @staticmethod
  def get_empty():
    return PdfFeatures([], [])
