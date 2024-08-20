from __future__ import annotations

from eschergraph.tools.reader import Reader


def test_reader() -> None:
  pdf_location: str = "test_file.pdf"
  text_location: str = "test_file.txt"
  pdf_reader: Reader = Reader(file_location=pdf_location, multimodal=False, overlap=0)
  text_reader: Reader = Reader(file_location=text_location, multimodal=False, overlap=0)

  pdf_reader.parse()
  text_reader.parse()
