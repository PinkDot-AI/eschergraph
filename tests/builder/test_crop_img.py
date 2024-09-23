from __future__ import annotations

from eschergraph.builder.reader.multi_modal.multi_modal_parser import (
  _crop_image_from_pdf_page,
)


def test_crop_image_negative_bbox() -> None:
  path: str = "test_files/Attention Is All You Need.pdf"
  page_num: int = 12
  bbox: list[float] = [-10.2, -10.1, -5.0, -5]

  img = _crop_image_from_pdf_page(path, page_num - 1, bbox)
  w, h = img.size
  assert w == 0
  assert h == 0


def test_crop_image_bbox_outside_page() -> None:
  path: str = "test_files/Attention Is All You Need.pdf"
  page_num: int = 12
  bbox: list[float] = [
    10000.1,
    10000.2,
    20000.3,
    20000.2,
  ]  # Far outside the typical page dimensions

  img = _crop_image_from_pdf_page(path, page_num - 1, bbox)
  w, h = img.size
  assert w == 0
  assert h == 0


def test_crop_image_zero_area_bbox() -> None:
  path: str = "test_files/Attention Is All You Need.pdf"
  page_num: int = 12
  bbox: list[float] = [100.0, 100.0, 100.0, 100.0]  # A box with no area

  img = _crop_image_from_pdf_page(path, page_num - 1, bbox)
  w, h = img.size
  assert w == 0
  assert h == 0
