from __future__ import annotations

from eschergraph.builder.reader.reader import Chunk
from eschergraph.builder.reader.reader import Reader


def test_reader_pdf() -> None:
  reader: Reader = Reader(
    file_location="test_files/Attention Is All You Need.pdf", multimodal=False
  )
  reader.parse()

  assert reader.chunks

  for chunk in reader.chunks:
    assert isinstance(chunk, Chunk)
