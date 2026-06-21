from __future__ import annotations


class GeminiService:
    assistant = "gemini"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    async def reply(
        self,
        messages: list[dict[str, str]],
        language: str,
    ) -> str:
        last = messages[-1]["content"] if messages else ""
        if language == "en":
            return (
                "Gemini Assistant integration is prepared and currently uses "
                "a safe stub. This conversation remains isolated and saved. "
                f"Last message: {last}"
            )
        return (
            "Интеграция Gemini Assistant подготовлена и пока использует "
            "безопасную заглушку. Диалог изолирован и сохранён. "
            f"Последнее сообщение: {last}"
        )
