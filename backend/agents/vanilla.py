"""
Vanilla adapter implementation using official OpenAI and Google clients.
"""

import asyncio
import os
import traceback
from typing import Literal

import google.generativeai as genai
from openai import AsyncOpenAI

from backend.agents.base_adapter import BaseAdapter


class VanillaAdapter(BaseAdapter):
    """
    Implements the BaseAdapter protocol using direct calls to LLM APIs.
    """

    client: AsyncOpenAI | genai.GenerativeModel

    def __init__(
        self,
        adapter_type: Literal["vanilla_openai", "vanilla_google"] = "vanilla_openai",
        model_name: str | None = None,
    ):
        self.adapter_type = adapter_type

        if self.adapter_type == "vanilla_openai":
            self.model_name = model_name or "gpt-4.1-mini"
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            self.client = AsyncOpenAI(api_key=api_key)
        elif self.adapter_type == "vanilla_google":
            self.model_name = model_name or "gemini-2.5-flash"
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model_name)
        else:
            raise ValueError(f"Unsupported adapter type: {self.adapter_type}")

    async def call_llm(self, prompt: str) -> str:
        """
        Calls the underlying language model with a given prompt.
        """
        try:
            if self.adapter_type == "vanilla_openai":
                if not isinstance(self.client, AsyncOpenAI):
                    raise TypeError("Client is not an AsyncOpenAI instance.")

                openai_response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2048,
                )
                openai_content: str = openai_response.choices[0].message.content or ""
                return openai_content

            elif self.adapter_type == "vanilla_google":
                if not isinstance(self.client, genai.GenerativeModel):
                    raise TypeError("Client is not a GenerativeModel instance.")

                print(
                    ">>> [Google Adapter] About to call generate_content in thread..."
                )
                # Run the synchronous SDK call in a separate thread
                google_response = await asyncio.to_thread(
                    self.client.generate_content, prompt
                )
                print(">>> [Google Adapter] Call to generate_content completed.")
                google_content: str = google_response.text
                return google_content

            else:
                # This should be unreachable due to the __init__ check
                raise ValueError(f"Unsupported adapter type: {self.adapter_type}")

        except Exception:
            # Aether's Rationale:
            # Catching a broad exception here to handle various API errors
            # (e.g., network issues, authentication failures, rate limits).
            # In a production system, this would be replaced with more granular
            # error handling and logging.
            error_details: str = str(traceback.format_exc())
            print(f"Error calling LLM: {error_details}")
            return f"Error: Could not get a response from the model. Details: {error_details}"
