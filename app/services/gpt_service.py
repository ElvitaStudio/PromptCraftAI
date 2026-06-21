from __future__ import annotations

from openai import AsyncOpenAI


class GPTService:
    assistant = "gpt"

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4.1-mini",
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = model

    async def reply(
        self,
        messages: list[dict[str, str]],
        language: str,
    ) -> str:
        if self.client is None:
            return self._stub(messages, language)
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

    @staticmethod
    def _stub(messages: list[dict[str, str]], language: str) -> str:
        last = messages[-1]["content"] if messages else ""
        if language == "en":
            return (
                "GPT Assistant stub is active. The conversation was saved "
                f"with its context. Last message: {last}"
            )
        return (
            "Активна заглушка GPT Assistant. Диалог и его контекст сохранены. "
            f"Последнее сообщение: {last}"
        )
