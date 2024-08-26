from __future__ import annotations

from pydantic import BaseModel

from eschergraph.tools.pdf_document_layout_analysis.pdf_features.rectangle import (
  Rectangle,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_token_type_labels.page_labels import (
  PageLabels,
)


class PdfLabels(BaseModel):
  pages: list[PageLabels] = list()

  def get_label_type(self, page_number: int, token_bounding_box: Rectangle):
    for page in self.pages:
      if page.number != page_number:
        continue

      return page.get_token_type(token_bounding_box)

    return 6
