"""Defines the protocol and shared exceptions for agent adapters."""

from typing import Protocol


class AdapterError(RuntimeError):
    """Raised when an upstream LLM request fails."""

    def __init__(self, provider: str, message: str):
        super().__init__(message)
        self.provider = provider


class BaseAdapter(Protocol):
    """
    Protocol for an agent adapter that can be called by the pipeline.
    """

    adapter_type: str

    async def call_llm(self, prompt: str) -> str:
        """
        Calls the underlying language model with a given prompt.
        """
        ...
