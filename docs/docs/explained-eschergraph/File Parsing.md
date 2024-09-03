---
sidebar_position: 1
---

# File Parsing

### PDF files

Parsing PDF files can be challenging due to difficulties in extracting and chunking text accurately. For PDF files, EscherGraph utilizes two open-source document layout models developed by [HURIDOCS](https://github.com/huridocs/pdf-document-layout-analysis), we use their lightweight LightGBM models to make it easy to setup and run the package. These models leverage XML data extracted by Poppler for analysis.

We are actively working on enhancing EscherGraph to be multimodal. The VGT (Vision Grid Transformer) model from HURIDOCS will enable this advancement, only this model is too large to run on a local device, and needs a GPU. 

For paragraph detection and chunking, we use their models within our parser.

```python
from eschergraph.tools.reader import Reader, Chunk
file_location = 'test_files/Attention is All You Need.pdf'

reader = Reader(
    file_location: file_location
)
reader.parse()
chunks = reader.chunks -> list[Chunk]
```

This is the Chunk object definition.

```python
@define
class Chunk:
  """The chunk object."""

  text: str
  chunk_id: int
  doc_id: UUID
  page_num: Optional[int]
  doc_name: str
```
### TXT files:
For TXT files, we use the Langchain recursive splitter, with a standard chunk size of 1500 characters and an overlap of 300 characters.
```python
from eschergraph.tools.reader import Reader
file_location = 'test_files/txt_file.txt'

reader = Reader(
    file_location = file_location,
    chunk_size = 1500,
    overlap = 300
)
reader.parse()
chunks = reader.chunks
```

## Poppler disclaimer
As mentioned previously, our PDF parser uses Poppler internally to convert PDF into XML. Therefore, you are required to have Poppler installed when building a graph from PDF files with our package. Unfortunately, it can be quite a hassle to install Poppler on Windows. In order to mitigate this, our package will automatically install Poppler on Windows, if not already present. We do this by checking if the required functionality is in the path, if not, then we download a Poppler binary from [poppler-windows](https://github.com/oschwartz10612/poppler-windows). The zip file is then extracted and placed in the package's source. It is only during runtime that the binary is placed in the PATH and executed. Hence, this will only occur within the process that runs EscherGraph whilst parsing a PDF.

We wanted to be fully transparent about this, since a package downloading and running binaries on your hardware can also be done with malicious intent. However, we have done this to make it as easy as possible for Windows users to use our package. If interested, the corresponding code can be found in `eschergraph/tools/fast_pdf_parse/parser.py`.