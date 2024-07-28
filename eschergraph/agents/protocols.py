from __future__ import annotations

from typing import Protocol

from eschergraph.agents.tools import Tool


class ExternalFactor(Protocol):
  """The interface that agents expect for external factors.

  The agent expects this protocol to be implemented for all
  external factors that it uses.
  """

  def get_tools(self) -> list[Tool]:
    """Get a list with all the tools for the agent.

    This function returns a list of tools that the agent can use.
    """
    ...
