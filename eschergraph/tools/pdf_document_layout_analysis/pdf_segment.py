from __future__ import annotations

from statistics import mode

from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_token import (
  PdfToken,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_features.rectangle import (
  Rectangle,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_token_type_labels.token_type import (
  TokenType,
)


class PdfSegment:
  def __init__(
    self,
    page_number: int,
    bounding_box: Rectangle,
    text_content: str,
    segment_type: TokenType,
    pdf_name: str = "",
  ):
    self.page_number = page_number
    self.bounding_box = bounding_box
    self.text_content = text_content
    self.segment_type = segment_type
    self.pdf_name = pdf_name

  @staticmethod
  def from_pdf_tokens(pdf_tokens: list[PdfToken], pdf_name: str = ""):
    text: str = " ".join([pdf_token.content for pdf_token in pdf_tokens])
    bounding_boxes = [pdf_token.bounding_box for pdf_token in pdf_tokens]
    segment_type = mode([token.token_type for token in pdf_tokens])
    return PdfSegment(
      pdf_tokens[0].page_number,
      Rectangle.merge_rectangles(bounding_boxes),
      text,
      segment_type,
      pdf_name,
    )
