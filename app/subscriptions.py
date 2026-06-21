from app.catalog import tr


def premium_text(language: str) -> str:
    return tr(
        language,
        "👑 Тарифы PromptCraft AI\n\n"
        "🆓 FREE\n"
        "• 1 вариант промпта\n"
        "• Уровни Simple и Advanced\n"
        "• История промптов\n\n"
        "━━━━━━━━━━━━\n"
        "⭐ PRO — 199 Stars / 30 дней\n"
        "• 2 варианта промпта\n"
        "• Все категории\n"
        "• Библиотека шаблонов\n"
        "• Prompt of the Day\n\n"
        "━━━━━━━━━━━━\n"
        "👑 PREMIUM — 399 Stars / 30 дней\n"
        "• Expert Mode\n"
        "• 3 варианта промпта\n"
        "• Все стили ответа\n"
        "• Все режимы программиста\n"
        "• Избранное\n"
        "• Экспорт TXT и Markdown\n\n"
        "Выберите тариф:",
        "👑 PromptCraft AI plans\n\n"
        "🆓 FREE\n"
        "• 1 prompt variant\n"
        "• Simple and Advanced levels\n"
        "• Prompt history\n\n"
        "━━━━━━━━━━━━\n"
        "⭐ PRO — 199 Stars / 30 days\n"
        "• 2 prompt variants\n"
        "• All categories\n"
        "• Prompt template library\n"
        "• Prompt of the Day\n\n"
        "━━━━━━━━━━━━\n"
        "👑 PREMIUM — 399 Stars / 30 days\n"
        "• Expert Mode\n"
        "• 3 prompt variants\n"
        "• All response styles\n"
        "• All developer modes\n"
        "• Favorites\n"
        "• TXT and Markdown export\n\n"
        "Choose a plan:",
    )
