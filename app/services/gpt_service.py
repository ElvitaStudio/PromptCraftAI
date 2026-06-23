from __future__ import annotations

from openai import AsyncOpenAI

from app.services.errors import AssistantConfigurationError


class GPTService:
    assistant = "gpt"

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4.1-mini",
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = model

    @property
    def is_configured(self) -> bool:
        return self.client is not None

    async def reply(
        self,
        messages: list[dict[str, str]],
        language: str,
    ) -> str:
        if self.client is None:
            raise AssistantConfigurationError(
                "OPENAI_API_KEY is not configured"
            )
        transcript = "\n".join(
            f"{item['role']}: {item['content']}" for item in messages
        )
        response = await self.client.responses.create(
            model=self.model,
            instructions=(
                "You are GPT Assistant inside PromptCraft AI Workspace. "
                "Continue the conversation using its full context. "
                f"Reply in {'English' if language == 'en' else 'Russian'}."
            ),
            input=transcript,
        )
        result = response.output_text.strip()
        if not result:
            raise ValueError("GPT Assistant returned an empty response")
        return result
