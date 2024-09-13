from __future__ import annotations

from eschergraph.builder.reader.multi_modal.crop_images import crop_image_from_pdf_page


def test_crop_image_negative_bbox():
  path = "test_files/Attention Is All You Need.pdf"
  page_num = 12
  bbox = [-10, -10, -5, -5]

  img = crop_image_from_pdf_page(path, page_num - 1, bbox)
  w, h = img.size
  assert w == 0
  assert h == 0


def test_crop_image_bbox_outside_page():
  path = "test_files/Attention Is All You Need.pdf"
  page_num = 12
  bbox = [10000, 10000, 20000, 20000]  # Far outside the typical page dimensions

  img = crop_image_from_pdf_page(path, page_num - 1, bbox)
  w, h = img.size
  assert w == 0
  assert h == 0


def test_crop_image_zero_area_bbox():
  path = "test_files/Attention Is All You Need.pdf"
  page_num = 12
  bbox = [100, 100, 100, 100]  # A box with no area

  img = crop_image_from_pdf_page(path, page_num - 1, bbox)
  w, h = img.size
  assert w == 0
  assert h == 0
