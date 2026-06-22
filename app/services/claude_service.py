from __future__ import annotations

from typing import Any

import httpx

from app.services.errors import (
    AssistantAPIError,
    AssistantConfigurationError,
)


class ClaudeService:
    assistant = "claude"
    endpoint = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-sonnet-4-6",
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.model = model
        self.client = client

    async def reply(
        self,
        messages: list[dict[str, str]],
        language: str,
    ) -> str:
        if not self.api_key:
            raise AssistantConfigurationError(
                "ANTHROPIC_API_KEY is not configured"
            )
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": (
                "You are Claude Assistant inside PromptCraft AI Workspace. "
                "Use the full conversation context and answer in "
                f"{'English' if language == 'en' else 'Russian'}."
            ),
            "messages": [
                {
                    "role": item["role"],
                    "content": item["content"],
                }
                for item in messages
                if item["role"] in {"user", "assistant"}
            ],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        if self.client is not None:
            response = await self.client.post(
                self.endpoint,
                headers=headers,
                json=payload,
            )
        else:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                )
        response.raise_for_status()
        data = response.json()
        result = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()
        if not result:
            raise AssistantAPIError(
                "Anthropic returned an empty response"
            )
        return result
