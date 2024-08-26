from __future__ import annotations

import os
from typing import Any

import requests
from requests import Response
from sentence_transformers import CrossEncoder

from eschergraph.agents.reranker import Reranker


class JinaReranker(Reranker):
  """A reranker that uses Jina's API to rerank a list of documents based on their relevance to a query.

  Methods:
      rerank(query: str, text_list: list[str], top_n: int) -> Optional[list[RerankerResult]]:
          Sends a request to Jina's API to rerank the provided text list according to the query.
  """

  def rerank(
    self, query: str, texts_list: list[str], top_n: int
  ) -> list[RerankerResult]:
    """Reranks a list of text documents based on their relevance to the query using Jina's API.

    Args:
        model_repo (str, optional): the hugginface repository of the reranker. Defaults to "jinaai/jina-reranker-v1-turbo-en".
    """
    self.model = CrossEncoder(model_repo, trust_remote_code=True)

  def rank(self, docs: list[str], query: str, top_n: int) -> List[Dict]:
    """Rank the documents based on the relevance to the query.

    Args:
        docs (list[str]): a list of strings containing information
        query (str): string of text to compare against
        top_n (int): amount of relevant results to be returned

    Returns:
        List[Dict]: A list of dicts containing the most relevant docs and their relevance scores
    """
    if len(docs) == 0:
      return []
    results = self.model.rank(query, docs, return_documents=True, top_k=top_n)

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
