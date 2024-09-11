from __future__ import annotations

import os

import requests

from eschergraph.tools.pdf_document_layout_analysis.pdf_parser_large.data_structure import (
  AnalysisResult,
)


# Function to call the /analyze_document endpoint
def pdf_parser_large(
  document_path: str, endpoint_url: str = "http://127.0.0.1:8000/analyze_document"
):
  if not os.path.isfile(document_path):
    raise FileNotFoundError(f"The file at {document_path} does not exist.")

  with open(document_path, "rb") as file:
    files = {"file": (os.path.basename(document_path), file, "application/pdf")}
    try:
      response = requests.post(endpoint_url, files=files)
      response.raise_for_status()  # Check if the request was successful
    except requests.RequestException as e:
      raise Exception(f"Error while calling API: {str(e)}")

    try:
      # Parse the JSON response
      data = response.json()
      # Validate and parse the response into the AnalysisResult model
      analysis_result = AnalysisResult(**data)
      return analysis_result
    except Exception as e:
      raise ValueError(f"Error parsing the response: {str(e)}")
