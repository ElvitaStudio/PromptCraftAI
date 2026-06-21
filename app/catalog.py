LANGUAGES = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

CATEGORIES = {
    "text": {"ru": "📝 Текст", "en": "📝 Text"},
    "images": {"ru": "🎨 Изображения", "en": "🎨 Images"},
    "video": {"ru": "🎬 Видео", "en": "🎬 Video"},
    "code": {"ru": "💻 Код", "en": "💻 Code"},
    "marketing": {"ru": "📣 Маркетинг", "en": "📣 Marketing"},
    "business": {"ru": "💼 Бизнес", "en": "💼 Business"},
    "study": {"ru": "🎓 Учеба", "en": "🎓 Study"},
}

AI_MODELS = {
    "chatgpt": "ChatGPT",
    "claude": "Claude",
    "gemini": "Gemini",
    "grok": "Grok",
    "midjourney": "Midjourney",
    "gpt_image": "GPT Image",
    "flux": "Flux",
    "kling": "Kling",
    "veo": "Veo",
    "runway": "Runway",
    "cursor": "Cursor",
    "claude_code": "Claude Code",
    "codex": "Codex",
}


def tr(language: str, ru: str, en: str) -> str:
    return en if language == "en" else ru
