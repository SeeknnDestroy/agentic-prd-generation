"""Defines the protocol for agent adapters.

This ensures that any agent implementation, whether a vanilla client or a
framework-based one (like CrewAI), can be used interchangeably by the
pipeline runner.
"""
from typing import Protocol


class BaseAdapter(Protocol):
    """
    Protocol for an agent adapter that can be called by the pipeline.
    """

    async def call_llm(self, prompt: str) -> str:
        """
        Calls the underlying language model with a given prompt.
        """
        ...
