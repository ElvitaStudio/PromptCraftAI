from __future__ import annotations

from app.catalog import AI_MODELS, CATEGORIES


DIFFICULTIES = {
    "simple": {"ru": "🟢 Simple", "en": "🟢 Simple"},
    "advanced": {"ru": "🔵 Advanced", "en": "🔵 Advanced"},
    "expert": {"ru": "👑 Expert", "en": "👑 Expert"},
}

RESPONSE_STYLES = {
    "short": {"ru": "📄 Short", "en": "📄 Short"},
    "detailed": {"ru": "📑 Detailed", "en": "📑 Detailed"},
    "professional": {"ru": "🎯 Professional", "en": "🎯 Professional"},
    "expert": {"ru": "🧠 Expert", "en": "🧠 Expert"},
}

WORKFLOWS = {"create", "optimize"}

CODING_ASSISTANTS = {"claude_code", "codex", "cursor"}


def validate_profile(
    category: str,
    target_ai: str,
    difficulty: str,
    response_style: str,
    workflow: str,
) -> None:
    if category not in CATEGORIES:
        raise ValueError("Unsupported category")
    if target_ai not in AI_MODELS:
        raise ValueError("Unsupported AI")
    if difficulty not in DIFFICULTIES:
        raise ValueError("Unsupported difficulty")
    if response_style not in RESPONSE_STYLES:
        raise ValueError("Unsupported response style")
    if workflow not in WORKFLOWS:
        raise ValueError("Unsupported workflow")


def profile_summary(
    language: str,
    category: str,
    target_ai: str,
    difficulty: str,
    response_style: str,
) -> str:
    category_label = CATEGORIES[category].get(language, CATEGORIES[category]["ru"])
    return (
        f"{category_label} · {AI_MODELS[target_ai]}\n"
        f"{DIFFICULTIES[difficulty][language]} · "
        f"{RESPONSE_STYLES[response_style][language]}"
    )
