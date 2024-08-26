from __future__ import annotations

from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_token import (
  PdfToken,
)


class Paragraph:
  def __init__(self, tokens: list[PdfToken], pdf_name: str = ""):
    self.tokens = tokens
    self.pdf_name = pdf_name

  def add_token(self, token: PdfToken):
    self.tokens.append(token)
