from __future__ import annotations

import os
import platform
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

from fast_trainer.model_configuration import (
  MODEL_CONFIGURATION as PARAGRAPH_EXTRACTION_CONFIGURATION,
)
from fast_trainer.ParagraphExtractorTrainer import ParagraphExtractorTrainer
from fast_trainer.PdfSegment import PdfSegment
from huggingface_hub import hf_hub_download
from pdf_features.PdfFeatures import PdfPage
from pdf_tokens_type_trainer.ModelConfiguration import ModelConfiguration
from pdf_tokens_type_trainer.TokenTypeTrainer import TokenTypeTrainer

from eschergraph.exceptions import ExternalDependencyException
from eschergraph.tools.fast_pdf_parser.models import PdfParsedSegment
from eschergraph.tools.fast_pdf_parser.pdf_features import PdfFeatures

ROOT_PATH: str = Path(__file__).parent.parent.absolute().as_posix()
MODELS_PATH: str = ROOT_PATH + "/fast_models"
BINS_PATH: Path = Path(__file__).parent.parent.parent / "bins"


def _download_and_unzip_for_windows() -> None:
  download_link: str = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.07.0-0/Release-24.07.0-0.zip"
  local_filename: Path = BINS_PATH / "Release-24.07.0-0.zip"
  urllib.request.urlretrieve(url=download_link, filename=local_filename.as_posix())
  extract_path: Path = BINS_PATH / "Release-24.07.0-0"
  original_path: Path = extract_path / "poppler-24.07.0"

  # Unpack the zip file
  with zipfile.ZipFile(local_filename.as_posix(), mode="r") as zip_ref:
    zip_ref.extractall(path=extract_path.as_posix())

  shutil.move(src=original_path.as_posix(), dst=BINS_PATH.as_posix())

  # Clean up the directories that are not needed
  os.remove(local_filename.as_posix())
  shutil.rmtree(extract_path.as_posix())


# Also add a script that downloads poppler
if platform.system() == "Windows":
  poppler_unpacked_path: Path = BINS_PATH / "poppler-24.07.0"

  # Check whether poppler has already been downloaded
  if not poppler_unpacked_path.exists():
    BINS_PATH.mkdir(exist_ok=True)

    _download_and_unzip_for_windows()

  poppler_path: Path = poppler_unpacked_path / "Library" / "bin"
  os.environ["PATH"] += ";" + poppler_path.as_posix()

if not shutil.which("pdftohtml"):
  raise ExternalDependencyException(
    "Poppler(pdftohtml) is missing from your system! Please install this to be able to parse pdf files!"
  )


class FastPdfParser:
  """The fast pdf parser that uses LightGBM models."""

  @staticmethod
  def parse(file_path: str) -> list[PdfParsedSegment]:
    """Use the fast LightGBM models to parse a PDF into segments.

    The models and the approach has been adapted from: https://github.com/huridocs/pdf-document-layout-analysis.
    All the credits to huridocs for their amazing work on this!

    Args:
      file_path (str): The path to the file to parse.

    Returns:
      A list of parsed pdf segments, where each pdf segment is a typed dictionary.
    """
    # Make sure the models are present
    FastPdfParser._download_models()

    xml_path = Path(tempfile.gettempdir()).as_posix() + "/pdf_etree.xml"
    pdf_features: Optional[PdfFeatures] = PdfFeatures.from_pdf_path(
      pdf_path=file_path, xml_path=xml_path
    )
    token_type_trainer: TokenTypeTrainer = TokenTypeTrainer(
      [pdf_features], ModelConfiguration()
    )
    token_type_trainer.set_token_types(
      model_path=MODELS_PATH + "/token_type_lightgbm.model"
    )
    trainer: ParagraphExtractorTrainer = ParagraphExtractorTrainer(
      pdfs_features=[pdf_features],
      model_configuration=PARAGRAPH_EXTRACTION_CONFIGURATION,
    )
    segments: list[PdfSegment] = trainer.get_pdf_segments(
      paragraph_extractor_model_path=MODELS_PATH
      + "/paragraph_extraction_lightgbm.model"
    )

    return [
      FastPdfParser._to_parsed_segment(segment, pdf_features.pages)  # type: ignore
      for segment in segments
    ]

  @staticmethod
  def _to_parsed_segment(
    pdf_segment: PdfSegment, pdf_pages: list[PdfPage]
  ) -> PdfParsedSegment:
    return {
      "left": pdf_segment.bounding_box.left,
      "top": pdf_segment.bounding_box.top,
      "width": pdf_segment.bounding_box.width,
      "height": pdf_segment.bounding_box.height,
      "page_number": pdf_segment.page_number,
      "page_width": pdf_pages[pdf_segment.page_number - 1].page_width,
      "page_height": pdf_pages[pdf_segment.page_number - 1].page_height,
      "text": pdf_segment.text_content,
      "type": pdf_segment.segment_type.name,
    }

  @staticmethod
  def _download_models() -> None:
    models_path: Path = Path(MODELS_PATH)

    # Create the path if it does not exist
    if not models_path.exists():
      models_path.mkdir(exist_ok=True, parents=True)

    tokens_type_model_path: Path = models_path / "token_type_lightgbm.model"
    paragraph_extraction_model_path: Path = (
      models_path / "paragraph_extraction_lightgbm.model"
    )

    if not tokens_type_model_path.exists():
      hf_hub_download(
        repo_id="HURIDOCS/pdf-document-layout-analysis",
        filename="token_type_lightgbm.model",
        local_dir=str(MODELS_PATH),
      )
    if not paragraph_extraction_model_path.exists():
      hf_hub_download(
        repo_id="HURIDOCS/pdf-document-layout-analysis",
        filename="paragraph_extraction_lightgbm.model",
        local_dir=str(MODELS_PATH),
      )