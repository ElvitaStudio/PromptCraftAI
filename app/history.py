from datetime import datetime, timezone

from app.catalog import AI_MODELS
from app.database import PromptRecord
from app.presentation import split_text


def _date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone().strftime("%d.%m.%Y %H:%M")


def history_chunks(
    records: list[PromptRecord],
    language: str,
) -> list[str]:
    if not records:
        return [
            "📭 История пока пустая. Создайте первый промпт."
            if language == "ru"
            else "📭 History is empty. Create your first prompt."
        ]
    header = "📜 История промптов" if language == "ru" else "📜 Prompt history"
    entries = []
    for index, record in enumerate(records, start=1):
        fragment = " ".join(record.prompt_text.split())
        if len(fragment) > 300:
            fragment = fragment[:297].rstrip() + "..."
        entries.append(
            f"{index}. {_date(record.created_at)} · "
            f"{AI_MODELS.get(record.target_ai, record.target_ai)}\n"
            f"🧩 {fragment}"
        )
    return split_text(header + "\n\n" + "\n\n".join(entries))
