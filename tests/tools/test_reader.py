from __future__ import annotations

from eschergraph.tools.reader import Chunk
from eschergraph.tools.reader import Reader


def test_reader_pdf() -> None:
  reader: Reader = Reader(
    file_location="test_files/Attention Is All You Need.pdf", multimodal=False
  )
  reader.parse()

  assert reader.chunks

  for chunk in reader.chunks:
    assert isinstance(chunk, Chunk)
