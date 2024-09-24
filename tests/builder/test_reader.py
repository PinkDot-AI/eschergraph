from __future__ import annotations

from uuid import uuid4

from eschergraph.builder.models import Chunk
from eschergraph.builder.reader.fast_pdf_parser.models import PdfParsedSegment
from eschergraph.builder.reader.multi_modal.data_structure import Paragraph
from eschergraph.builder.reader.reader import Reader


def test_chunk_paragraphs() -> None:
  reader: Reader = Reader(
    file_location="test_files/Attention Is All You Need.pdf",
    multimodal=False,
    optimal_tokens=400,
  )
  parsed_paragraphs: list[Paragraph] = reader._get_document_analysis()
  reader._chunk_paragraphs(parsed_paragraphs)

  chunks: list[Chunk] = reader.chunks

  last_chunk_id = -1
  last_page_num = -1
  for c in chunks:
    assert c.chunk_id > last_chunk_id
    last_chunk_id = c.chunk_id

    if c.page_num:
      assert c.page_num >= last_page_num
      last_page_num = c.page_num

    # chunk whether optimal tokens does not have too much varience
    assert reader._count_tokens(c.text) <= 430


def test_handle_plain_text() -> None:
  reader = Reader(file_location="test_files/txt_file.txt")
  reader.chunk_size = 800
  reader.overlap = 100
  reader.doc_id = uuid4()
  reader.chunks = []

  reader._parse_plain_text()

  assert len(reader.chunks) > 0  # Ensure chunks were created
  assert all(isinstance(chunk, Chunk) for chunk in reader.chunks)
  assert reader.chunks[0].doc_id == reader.doc_id
  assert reader.chunks[0].page_num is None
  assert isinstance(reader.chunks[0].text, str)
  for chunk in reader.chunks:
    assert len(chunk.text) <= reader.chunk_size


def test_contains_non_alpha() -> None:
  input_string1: str = "ThisIsAllAlpha"
  a: bool = Reader._contains_many_non_alpha(input_string1)
  assert a is False, "The string contains only alphabets, should return False."

  input_string2: str = "1234!@#$"
  b: bool = Reader._contains_many_non_alpha(input_string2)
  assert b is True, "The string contains only non-alpha characters, should return True."

  input_string3: str = "M123!@#"
  c: bool = Reader._contains_many_non_alpha(input_string3)
  assert c is True, "Non-alpha characters exceed the threshold, should return True."

  input_string4: str = "Test 123 with spaces!"
  d: bool = Reader._contains_many_non_alpha(input_string4)
  assert (
    d is False
  ), "Whitespaces should be ignored, and the non-alpha characters do not exceed the threshold."

  input_string5: str = ""
  e: bool = Reader._contains_many_non_alpha(input_string5)
  assert e is False, "Empty string should return False."

  input_string6: str = "abc123"  # 50% non-alpha characters (3/6)
  threshold_percentage = 0.50
  f: bool = Reader._contains_many_non_alpha(input_string6, threshold_percentage)
  assert (
    f is False
  ), "At the threshold, should return False as it's not exceeding the threshold."


def test_to_paragraph_structure() -> None:
  # Create example pdf_segment objects similar to what was provided
  pdf_segments: list[PdfParsedSegment] = [
    {
      "left": 108,
      "top": 110,
      "width": 397,
      "height": 30,
      "page_number": 12,
      "page_width": 612,
      "page_height": 792,
      "text": "[26] David McClosky, Eugene Charniak...",
      "type": "LIST_ITEM",
    },
    {
      "left": 108,
      "top": 155,
      "width": 396,
      "height": 20,
      "page_number": 12,
      "page_width": 612,
      "page_height": 792,
      "text": "[27] Ankur Parikh, Oscar TÃ¤ckstrÃ¶m...",
      "type": "LIST_ITEM",
    },
    {
      "left": 108,
      "top": 189,
      "width": 396,
      "height": 20,
      "page_number": 12,
      "page_width": 612,
      "page_height": 792,
      "text": "[28] Romain Paulus, Caiming Xiong...",
      "type": "TEXT",
    },
    {
      "left": 108,
      "top": 280,
      "width": 396,
      "height": 20,
      "page_number": 12,
      "page_width": 612,
      "page_height": 792,
      "text": "[30] Ofir Press and Lior Wolf...",
      "type": "SECTION_HEADER",
    },
  ]

  expected_results: list[dict[str, str | int | None]] = [
    {
      "id": 1,
      "role": None,
      "content": "[26] David McClosky, Eugene Charniak...",
      "page_num": 12,
    },
    {
      "id": 2,
      "role": None,
      "content": "[27] Ankur Parikh, Oscar TÃ¤ckstrÃ¶m...",
      "page_num": 12,
    },
    {
      "id": 3,
      "role": None,
      "content": "[28] Romain Paulus, Caiming Xiong...",
      "page_num": 12,
    },
    {
      "id": 4,
      "role": "sectionHeading",
      "content": "[30] Ofir Press and Lior Wolf...",
      "page_num": 12,
    },
  ]

  # Compare the results
  for i, pdf_segment in enumerate(pdf_segments):
    result: Paragraph = Reader._to_paragraph_structure(pdf_segment, id=i + 1)
    assert result == expected_results[i]
