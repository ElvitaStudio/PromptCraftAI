from app.catalog import AI_MODELS, CATEGORIES
from app.database import PromptRecord

EXTRA_AI_NAMES = {"deepseek": "DeepSeek"}


def prompt_txt(record: PromptRecord) -> bytes:
    return record.prompt_text.strip().encode("utf-8")


def prompt_markdown(record: PromptRecord) -> bytes:
    category = CATEGORIES.get(record.category, {}).get(
        record.language,
        record.category,
    )
    target_ai = AI_MODELS.get(
        record.target_ai,
        EXTRA_AI_NAMES.get(record.target_ai, record.target_ai),
    )
    text = (
        "# PromptCraft AI\n\n"
        f"- **AI:** {target_ai}\n"
        f"- **Category:** {category}\n"
        f"- **Language:** {record.language.upper()}\n\n"
        "## Prompt\n\n"
        f"{record.prompt_text.strip()}\n"
    )
    return text.encode("utf-8")
