"""Vanilla adapter implementation using official OpenAI and Google clients."""

import asyncio
from importlib import import_module
from time import perf_counter
from typing import Literal

import structlog

from backend.agents.base_adapter import AdapterError, BaseAdapter

logger = structlog.get_logger(__name__)


class VanillaAdapter(BaseAdapter):
    """
    Implements the BaseAdapter protocol using direct calls to LLM APIs.
    """

    def __init__(
        self,
        adapter_type: Literal["vanilla_openai", "vanilla_google"] = "vanilla_openai",
        *,
        openai_api_key: str | None = None,
        google_api_key: str | None = None,
        openai_model: str = "gpt-4.1-mini",
        google_model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
        request_timeout_seconds: float = 60.0,
    ) -> None:
        self.adapter_type = adapter_type
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.request_timeout_seconds = request_timeout_seconds
        self._openai_api_key = openai_api_key
        self._google_api_key = google_api_key

        if self.adapter_type == "vanilla_openai":
            self.model_name = openai_model
            if not self._openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
        elif self.adapter_type == "vanilla_google":
            self.model_name = google_model
            if not self._google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
        else:
            raise ValueError(f"Unsupported adapter type: {self.adapter_type}")

    async def call_llm(self, prompt: str) -> str:
        """
        Calls the underlying language model with a given prompt.
        """
        started_at = perf_counter()
        try:
            if self.adapter_type == "vanilla_openai":
                response = await self._call_openai(prompt)
            else:
                response = await self._call_google(prompt)

            logger.info(
                "llm_call_succeeded",
                adapter=self.adapter_type,
                model=self.model_name,
                duration_seconds=round(perf_counter() - started_at, 3),
            )
            return response
        except AdapterError:
            logger.warning(
                "llm_call_failed",
                adapter=self.adapter_type,
                model=self.model_name,
                duration_seconds=round(perf_counter() - started_at, 3),
                exc_info=True,
            )
            raise

    async def _call_openai(self, prompt: str) -> str:
        """Call the OpenAI Chat Completions API."""
        try:
            openai_module = import_module("openai")
            async_openai_cls = openai_module.AsyncOpenAI
        except ModuleNotFoundError as exc:
            raise AdapterError("openai", "The OpenAI SDK is not installed.") from exc

        client = async_openai_cls(
            api_key=self._openai_api_key,
            timeout=self.request_timeout_seconds,
        )
        try:
            openai_response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
            )
            openai_content: str = openai_response.choices[0].message.content or ""
        except Exception as exc:
            raise AdapterError("openai", f"OpenAI request failed: {exc}") from exc
        finally:
            await client.close()

        if not openai_content.strip():
            raise AdapterError("openai", "OpenAI returned an empty response.")
        return openai_content

    async def _call_google(self, prompt: str) -> str:
        """Call the Google GenAI API using the supported SDK."""
        try:
            genai_module = import_module("google.genai")
            types_module = import_module("google.genai.types")
        except ModuleNotFoundError as exc:
            raise AdapterError(
                "google", "The Google GenAI SDK is not installed."
            ) from exc

        client = genai_module.Client(api_key=self._google_api_key)
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=types_module.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                ),
            )
        except Exception as exc:
            raise AdapterError("google", f"Google request failed: {exc}") from exc
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                await asyncio.to_thread(close)

        google_content = getattr(response, "text", "") or ""
        if not google_content.strip():
            raise AdapterError("google", "Google returned an empty response.")
        return google_content
