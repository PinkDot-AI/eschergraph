from __future__ import annotations


class Estimator:
  """This is a class for estimating the cost and time to build a graph from a document."""

  @staticmethod
  def get_cost_indication(total_tokens: int, model: str) -> float:
    """Estimates the cost based on the number of tokens and the model used.

    Args:
        total_tokens (int): The total number of tokens.
        model (str): The model used for estimation ('gpt-4o' or 'gpt-4o-mini').

    Returns:
        float: The estimated cost of processing.
    """
    # Initialize variables
    prompt_cost: float = 0.0
    completion_cost: float = 0.0

    # for each chunk 2 llm calls are performed, but also for the node machter an average of 2 llm calls per page.
    # Also some calls for the community building are used. We estimated it to be 2.5 llm calls per tokens.
    llm_calls_per_token_estimation = 2.5

    # Assumed that completion tokens are equal to prompt tokens
    if model == "gpt-4o":
      prompt_cost = (total_tokens / 1e6) * 5.00
      completion_cost = (total_tokens / 1e6) * 15.00
    elif model == "gpt-4o-mini":
      prompt_cost = (total_tokens / 1e6) * 0.150
      completion_cost = (total_tokens / 1e6) * 0.600
    else:
      raise ValueError("Invalid model specified.")

    building_cost: float = prompt_cost + (completion_cost / 4)
    return round(building_cost * llm_calls_per_token_estimation, 4)

  @staticmethod
  def get_time_indication(num_chunks: int, model: str) -> str:
    """Estimates the time required to process the document based on the number of chunks and the model used.

    Args:
        num_chunks (int): The number of chunks to process.
        model (str): The model used for estimation ('gpt-4o' or 'gpt-4o-mini').

    Returns:
        str: The estimated time to complete the processing, either in seconds or minutes.
    """
    # Determine average time per chunk based on model
    average_time_per_chunk: int = 4 if model == "gpt-4o" else 2

    max_workers: int = 2  # as used in ThreadPoolExecutor

    # If number of chunks is less than or equal to max_workers,
    # the time taken would be approximately the time for one chunk.
    if num_chunks <= max_workers:
      estimated_time = average_time_per_chunk
    else:
      # Calculate the time for full batches and any remaining chunks
      full_batches = num_chunks // max_workers
      remaining_chunks = num_chunks % max_workers

      estimated_time = full_batches * average_time_per_chunk
      if remaining_chunks > 0:
        estimated_time += average_time_per_chunk

    node_mathcer_delay = num_chunks * average_time_per_chunk
    community_building_delay = num_chunks * average_time_per_chunk

    estimated_time = estimated_time + node_mathcer_delay + community_building_delay

    # If the estimated time is more than 60 seconds, return time in minutes
    if estimated_time > 60:
      minutes = round(estimated_time / 60, 3)
      return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
      return f"{round(estimated_time, 3)} seconds"
