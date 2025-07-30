"""
Vanilla adapter implementation using official OpenAI and Google clients.
"""
from backend.agents.base_adapter import BaseAdapter


class VanillaAdapter(BaseAdapter):
    """
    Implements the BaseAdapter protocol using direct calls to LLM APIs.
    """

    async def call_llm(self, prompt: str) -> str:
        # Aether's Rationale:
        # This is a placeholder implementation. The actual logic will be added
        # in a subsequent step. For now, it returns a simple string to fulfill
        # the contract.
        return f"Response to: {prompt}"
