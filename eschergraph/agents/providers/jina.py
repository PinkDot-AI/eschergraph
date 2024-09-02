from __future__ import annotations

import os
from typing import Any

import requests
from attr import define
from requests import Response
from sentence_transformers import CrossEncoder

from eschergraph.agents.reranker import Reranker
from eschergraph.agents.reranker import RerankerResult
from eschergraph.exceptions import CredentialException
from eschergraph.exceptions import ExternalProviderException


@define
class JinaReranker(Reranker):
  """A reranker that uses Jina's API to rerank a list of documents based on their relevance to a query.

  Methods:
      rerank(query: str, text_list: list[str], top_n: int) -> Optional[list[RerankerResult]]:
          Sends a request to Jina's API to rerank the provided text list according to the query.
      get_model_name() -> str: returns the string of the model name
  """

  required_credentials: list[str] = ["JINA_API_KEY"]
  model: str = "jina-reranker-v2-base-multilingual"

  def get_model_name(self) -> str:
    """Returns the name of the model."""
    return self.model

  def rerank(
    self, query: str, text_list: list[str], top_n: int
  ) -> list[RerankerResult]:
    """Reranks a list of text documents based on their relevance to the query using Jina's API.

    Args:
        query (str): The query string for which documents are being reranked.
        text_list (list[str]): The list of documents (texts) to be reranked.
        top_n (int): The number of top relevant documents to return.

    Returns:
        Optional[list[RerankerResult]]: A list of reranked items with their relevance scores and text,
        or None if the request fails.
    """
    if not text_list:
      return []

    api_key: str = os.getenv("JINA_API_KEY")

    if not api_key:
      raise CredentialException("No API key for the Jina Reranker has been set")

    url = "https://api.jina.ai/v1/rerank"
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}",
    }
    data = {
      "model": self.model,
      "query": query,
      "documents": text_list,
      "top_n": top_n,
    }

    try:
      response: Response = requests.post(url, headers=headers, json=data)
      response.raise_for_status()
      response_json: Any = response.json()

      return [
        RerankerResult(
          index=r["index"],
          relevance_score=r["relevance_score"],
          text=r["document"]["text"],
        )
        for r in response_json.get("results", [])
      ]

    except requests.RequestException as e:
      raise ExternalProviderException(f"Request failed: {e}")
    except ValueError as e:
      raise ExternalProviderException(f"Something went wrong parsing the resulf: {e}")


class JinaRerankerTurbo(Reranker):
  """A reranker that uses a local model downloaded via the sentence_transformers library.

  Methods:
      rerank(docs: list[str], query: str, top_n: int) -> Optional[list[RerankerResult]]:
          Reranks the provided list of documents using the locally hosted model.
  """

  required_credentials: list[str] = []

  def __init__(self) -> None:
    """Initializes the JinaRerankerTurbo with a pre-trained model."""
    self.model: CrossEncoder = CrossEncoder(
      "jinaai/jina-reranker-v1-turbo-en", trust_remote_code=True
    )

  def rerank(
    self, query: str, text_list: list[str], top_n: int
  ) -> list[RerankerResult]:
    """Reranks a list of text documents based on their relevance to the query using the locally hosted model.

    Args:
        text_list (list[str]): The list of documents (texts) to be reranked.
        query (str): The query string for which documents are being reranked.
        top_n (int): The number of top relevant documents to return.

    Returns:
        Optional[list[RerankerResult]]: A list of reranked items with their relevance scores and text.
    """
    if not text_list:
      return []

    # Perform the ranking
    results = self.model.rank(query, text_list, return_documents=True, top_k=top_n)

    # Convert results to list of RerankerResult
    try:
      reranked_items = [
        RerankerResult(
          index=int(r["corpus_id"]),
          relevance_score=float(r["score"]),
          text=str(r["text"]),
        )
        for r in results
      ]

      return reranked_items
    except (KeyError, TypeError):
      raise ExternalProviderException(
        "Something went wrong obtaining the reranker results."
      )
