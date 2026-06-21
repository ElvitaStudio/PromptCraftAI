TELEGRAM_TEXT_LIMIT = 4096


def split_text(text: str, limit: int = TELEGRAM_TEXT_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            chunks.append(rest)
            break
        split_at = rest.rfind("\n", 0, limit + 1)
        if split_at < limit // 2:
            split_at = rest.rfind(" ", 0, limit + 1)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(rest[:split_at].strip())
        rest = rest[split_at:].strip()
    return [chunk for chunk in chunks if chunk]


def prompt_result_chunks(text: str, language: str) -> list[str]:
    header = "✨ Готовый промпт" if language == "ru" else "✨ Ready prompt"
    footer = "━━━━━━━━━━━━\n🚀 PromptCraft AI"
    complete = f"{header}\n\n{text.strip()}\n\n{footer}"
    return split_text(complete)
