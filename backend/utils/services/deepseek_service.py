from __future__ import annotations

"""Service for interacting with the DeepSeek chat completions API."""

import asyncio
import json
import logging
from typing import AsyncGenerator, AsyncIterator, Optional

import httpx


logger = logging.getLogger(__name__)


class DeepSeekService:
    """Wrapper around an OpenAI-compatible DeepSeek streaming chat endpoint."""

    def __init__(self, api_key: Optional[str], api_base: str) -> None:
        self._api_key = api_key
        self._api_base = api_base.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._api_base, timeout=30.0)

    async def astream_chat(
        self,
        system_prompt: str,
        user_content: str,
        model: str = "deepseek-chat",
    ) -> AsyncIterator[str]:
        """
        Stream chat completion tokens from DeepSeek.

        Yields partial text chunks as they arrive from the API.
        """

        if not self._api_key:
            logger.error("DEEPSEEK_API_KEY is not configured")
            raise RuntimeError("DeepSeek API key is missing")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "stream": True,
        }

        try:
            async with self._client.stream(
                "POST",
                "/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[len("data: ") :].strip()
                    else:
                        data_str = line.strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"]
                        content = delta.get("content")
                        if content:
                            yield content
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Failed to parse DeepSeek stream chunk: %s", exc)
                        continue
        except httpx.HTTPError as exc:
            logger.error("Error while calling DeepSeek API: %s", exc)
            raise

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

