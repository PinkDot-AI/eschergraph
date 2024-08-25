from __future__ import annotations

from pydantic import BaseModel

from eschergraph.tools.pdf_document_layout_analysis.pdf_features.rectangle import (
  Rectangle,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_token_type_labels.label import (
  Label,
)


class PageLabels(BaseModel):
  number: int
  labels: list[Label]

  def add_label(self, label: Label):
    self.labels.append(label)

  def get_token_type(self, token_bounding_box: Rectangle):
    intersection_percentage = 0
    token_type = 6
    sorted_labels_by_area = sorted(self.labels, key=lambda x: x.area())
    for label in sorted_labels_by_area:
      if label.intersection_percentage(token_bounding_box) > intersection_percentage:
        intersection_percentage = label.intersection_percentage(token_bounding_box)
        token_type = label.label_type
      if intersection_percentage > 95:
        return token_type

    return token_type
