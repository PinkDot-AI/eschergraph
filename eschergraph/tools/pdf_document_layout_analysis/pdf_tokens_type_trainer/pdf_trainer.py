from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np

from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_features import (
  PdfFeatures,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_font import PdfFont
from eschergraph.tools.pdf_document_layout_analysis.pdf_features.pdf_token import (
  PdfToken,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_features.rectangle import (
  Rectangle,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_token_type_labels.token_type import (
  TokenType,
)
from eschergraph.tools.pdf_document_layout_analysis.pdf_tokens_type_trainer.model_configuration import (
  ModelConfiguration,
)


class PdfTrainer:
  def __init__(
    self,
    pdfs_features: list[PdfFeatures],
    model_configuration: ModelConfiguration = None,
  ):
    self.pdfs_features = pdfs_features
    self.model_configuration = (
      model_configuration if model_configuration else ModelConfiguration()
    )

  def get_model_input(self) -> np.ndarray:
    pass

  @staticmethod
  def features_rows_to_x(features_rows):
    if not features_rows:
      return np.zeros((0, 0))

    x = np.zeros(((len(features_rows)), len(features_rows[0])))
    for i, v in enumerate(features_rows):
      x[i] = v
    return x

  def loop_tokens(self):
    for pdf_features in self.pdfs_features:
      for page, token in pdf_features.loop_tokens():
        yield token

  @staticmethod
  def get_padding_token(segment_number: int, page_number: int):
    return PdfToken(
      page_number,
      "pad_token",
      "",
      PdfFont("pad_font_id", False, False, 0.0, "#000000"),
      segment_number,
      Rectangle(0, 0, 0, 0),
      TokenType.TEXT,
    )

  # Models are already downloaded
  def predict(self, model_path: str | Path = None):
    x = self.get_model_input()

    if not x.any():
      return self.pdfs_features

    lightgbm_model = lgb.Booster(model_file=model_path)
    return lightgbm_model.predict(x)
