from typing import Dict, List
from sentence_transformers import CrossEncoder


class JinaReranker:
  """The reranker using Jina's model."""

  def __init__(self, model_repo="jinaai/jina-reranker-v1-turbo-en"):
    """Initialize the reranker model.

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

    for r in results:
      r["relevance_score"] = r.pop("score", None)
      r["index"] = r.pop("corpus_id", None)

    return results
