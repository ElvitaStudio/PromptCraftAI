from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.catalog import AI_MODELS, CATEGORIES, LANGUAGES
from app.programmer_templates import PROGRAMMER_TEMPLATES
from app.prompt_profiles import DIFFICULTIES, RESPONSE_STYLES
from app.templates import TEMPLATE_GROUPS, TEMPLATES, templates_for_group

PAYMENT_CALLBACK_PREFIX = "payment"


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"language:{code}",
                )
            ]
            for code, label in LANGUAGES.items()
        ]
    )


def workflow_keyboard(
    language: str,
    has_saved_settings: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=(
                    "✍ Создать промпт"
                    if language == "ru"
                    else "✍ Create Prompt"
                ),
                callback_data="workflow:create",
            ),
            InlineKeyboardButton(
                text=(
                    "🔧 Улучшить промпт"
                    if language == "ru"
                    else "🔧 Optimize Prompt"
                ),
                callback_data="workflow:optimize",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📜 История" if language == "ru" else "📜 History",
                callback_data="nav:history",
            ),
            InlineKeyboardButton(
                text="⭐ Избранное" if language == "ru" else "⭐ Favorites",
                callback_data="nav:favorites",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📚 Шаблоны" if language == "ru" else "📚 Templates",
                callback_data="nav:templates",
            ),
            InlineKeyboardButton(
                text=(
                    "🔥 Промпт дня"
                    if language == "ru"
                    else "🔥 Prompt of the Day"
                ),
                callback_data="nav:daily",
            ),
        ],
        [
            InlineKeyboardButton(
                text="👑 Premium",
                callback_data="nav:premium",
            ),
            InlineKeyboardButton(
                text="⚙️ Настройки" if language == "ru" else "⚙️ Settings",
                callback_data="nav:settings",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 Prompt Chat",
                callback_data="promptchat:start",
            )
        ],
    ]
    if has_saved_settings:
        rows.insert(
            2,
            [
                InlineKeyboardButton(
                    text=(
                        "⚡ Последние настройки"
                        if language == "ru"
                        else "⚡ Last settings"
                    ),
                    callback_data="settings:last",
                )
            ],
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def categories_keyboard(
    language: str,
    selected: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    items = list(CATEGORIES.items())
    for index in range(0, len(items), 2):
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        ("✓ " if code == selected else "")
                        + labels.get(language, labels["ru"])
                    ),
                    callback_data=f"category:{code}",
                )
                for code, labels in items[index:index + 2]
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ai_models_keyboard(
    category: str,
    selected: str | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=("✓ " if code == selected else "") + name,
            callback_data=f"ai:{category}:{code}",
        )
        for code, name in AI_MODELS.items()
    ]
    rows = [buttons[index:index + 2] for index in range(0, len(buttons), 2)]
    rows.append(
        [InlineKeyboardButton(text="⬅️", callback_data="nav:categories")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mode_keyboard(
    category: str,
    target_ai: str,
    language: str = "en",
) -> InlineKeyboardMarkup:
    prefix = f"mode:{category}:{target_ai}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=DIFFICULTIES["simple"][language],
                    callback_data=f"{prefix}:simple",
                ),
                InlineKeyboardButton(
                    text=DIFFICULTIES["advanced"][language],
                    callback_data=f"{prefix}:advanced",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=DIFFICULTIES["expert"][language],
                    callback_data=f"{prefix}:expert",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✨ 3 variants",
                    callback_data=f"{prefix}:variants",
                )
            ],
        ]
    )


def response_style_keyboard(
    category: str,
    target_ai: str,
    language: str,
) -> InlineKeyboardMarkup:
    prefix = f"style:{category}:{target_ai}"
    items = [
        (code, RESPONSE_STYLES[code])
        for code in ("short", "detailed", "professional", "expert")
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=labels[language],
                    callback_data=f"{prefix}:{code}",
                )
                for code, labels in items[index:index + 2]
            ]
            for index in range(0, len(items), 2)
        ]
    )


def programmer_modes_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=item.title(language),
            callback_data=f"devmode:{item.code}",
        )
        for item in PROGRAMMER_TEMPLATES.values()
    ]
    rows = [buttons[index:index + 2] for index in range(0, len(buttons), 2)]
    rows.append(
        [
            InlineKeyboardButton(
                text=(
                    "Пропустить →" if language == "ru" else "Skip →"
                ),
                callback_data="devmode:skip",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def prompt_actions_keyboard(
    prompt_id: int,
    language: str = "ru",
) -> InlineKeyboardMarkup:
    labels = {
        "copy": "📋 Копировать" if language == "ru" else "📋 Copy",
        "improve": "✨ Улучшить" if language == "ru" else "✨ Improve",
        "shorter": "📏 Короче" if language == "ru" else "📏 Shorter",
        "details": "📝 Подробнее" if language == "ru" else "📝 More details",
        "translate": (
            "🇬🇧 Перевести на английский"
            if language == "ru"
            else "🇬🇧 Translate to English"
        ),
        "variant": (
            "🔄 Другой вариант"
            if language == "ru"
            else "🔄 Another variant"
        ),
        "favorite": "⭐ В избранное" if language == "ru" else "⭐ Favorite",
    }
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=labels["copy"],
                    callback_data=f"prompt:copy:{prompt_id}",
                ),
                InlineKeyboardButton(
                    text=labels["improve"],
                    callback_data=f"prompt:improve:{prompt_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=labels["shorter"],
                    callback_data=f"prompt:shorter:{prompt_id}",
                ),
                InlineKeyboardButton(
                    text=labels["details"],
                    callback_data=f"prompt:details:{prompt_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=labels["translate"],
                    callback_data=f"prompt:translate_en:{prompt_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["variant"],
                    callback_data=f"prompt:variant:{prompt_id}",
                ),
                InlineKeyboardButton(
                    text=labels["favorite"],
                    callback_data=f"prompt:favorite:{prompt_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📄 Export TXT",
                    callback_data=f"prompt:export_txt:{prompt_id}",
                ),
                InlineKeyboardButton(
                    text="📝 Export MD",
                    callback_data=f"prompt:export_md:{prompt_id}",
                ),
            ],
        ]
    )


def templates_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=labels[1] if language == "en" else labels[0],
                    callback_data=f"tplgroup:{group}",
                )
            ]
            for group, labels in TEMPLATE_GROUPS.items()
        ]
    )


def template_items_keyboard(
    group: str,
    language: str,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=item.title(language),
                callback_data=f"template:{item.code}",
            )
        ]
        for item in templates_for_group(group)
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад" if language == "ru" else "⬅️ Back",
                callback_data="nav:templates",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def favorites_keyboard(
    favorites: list[tuple[int, str]],
    language: str,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{index}. {title}"[:64],
                callback_data=f"favorite:open:{favorite_id}",
            )
        ]
        for index, (favorite_id, title) in enumerate(favorites, 1)
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Новый промпт" if language == "ru" else "➕ New prompt",
                callback_data="nav:categories",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def premium_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Pro — 199 Stars",
                    callback_data="payment:pro",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Premium — 399 Stars",
                    callback_data="payment:premium",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "🎁 Пригласить друга"
                        if language == "ru"
                        else "🎁 Invite a friend"
                    ),
                    callback_data="payment:invite",
                )
            ],
        ]
    )


def settings_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Язык" if language == "ru" else "🌐 Language",
                    callback_data="settings:language",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "🎨 Стиль ответа"
                        if language == "ru"
                        else "🎨 Response style"
                    ),
                    callback_data="settings:style",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "🧠 Уровень генерации"
                        if language == "ru"
                        else "🧠 Generation level"
                    ),
                    callback_data="settings:difficulty",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "🤖 AI по умолчанию"
                        if language == "ru"
                        else "🤖 Default AI"
                    ),
                    callback_data="settings:ai",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "📋 Формат экспорта"
                        if language == "ru"
                        else "📋 Export format"
                    ),
                    callback_data="settings:export",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню" if language == "ru" else "⬅️ Main menu",
                    callback_data="nav:menu",
                )
            ],
        ]
    )


def settings_styles_keyboard(language: str) -> InlineKeyboardMarkup:
    labels = {
        "professional": "🎯 Professional",
        "detailed": "📑 Detailed",
        "concise": "📄 Concise",
        "creative": "🎨 Creative",
    }
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"pref:style:{code}",
                )
            ]
            for code, label in labels.items()
        ]
        + [[
            InlineKeyboardButton(
                text="⬅️ Назад" if language == "ru" else "⬅️ Back",
                callback_data="nav:settings",
            )
        ]]
    )


def settings_difficulty_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=DIFFICULTIES[code][language],
                    callback_data=f"pref:difficulty:{code}",
                )
            ]
            for code in ("simple", "advanced", "expert")
        ]
        + [[
            InlineKeyboardButton(
                text="⬅️ Назад" if language == "ru" else "⬅️ Back",
                callback_data="nav:settings",
            )
        ]]
    )


def settings_ai_keyboard(language: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=name,
            callback_data=f"pref:ai:{code}",
        )
        for code, name in AI_MODELS.items()
    ]
    rows = [buttons[index:index + 2] for index in range(0, len(buttons), 2)]
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад" if language == "ru" else "⬅️ Back",
            callback_data="nav:settings",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_export_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 TXT",
                    callback_data="pref:export:txt",
                ),
                InlineKeyboardButton(
                    text="📝 Markdown",
                    callback_data="pref:export:markdown",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад" if language == "ru" else "⬅️ Back",
                    callback_data="nav:settings",
                )
            ],
        ]
    )


def history_list_keyboard(
    prompts: list[tuple[int, str]],
    page: int,
    total_pages: int,
    language: str,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{index}. {title}"[:64],
                callback_data=f"history:open:{prompt_id}:{page}",
            )
        ]
        for index, (prompt_id, title) in enumerate(prompts, page * 5 + 1)
    ]
    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"history:page:{page - 1}",
            )
        )
    navigation.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="history:noop",
        )
    )
    if page + 1 < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"history:page:{page + 1}",
            )
        )
    rows.append(navigation)
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Главное меню" if language == "ru" else "⬅️ Main menu",
            callback_data="nav:menu",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def history_prompt_keyboard(
    prompt_id: int,
    page: int,
    language: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "♻️ Использовать снова"
                        if language == "ru"
                        else "♻️ Use again"
                    ),
                    callback_data=f"history:reuse:{prompt_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "⭐ В избранное"
                        if language == "ru"
                        else "⭐ Add to favorites"
                    ),
                    callback_data=f"history:favorite:{prompt_id}",
                ),
                InlineKeyboardButton(
                    text="📤 Экспорт" if language == "ru" else "📤 Export",
                    callback_data=f"history:export:{prompt_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К истории" if language == "ru" else "⬅️ History",
                    callback_data=f"history:page:{page}",
                )
            ],
        ]
    )


def prompt_chat_ai_keyboard(language: str) -> InlineKeyboardMarkup:
    models = {
        "claude_code": "Claude Code",
        "codex": "Codex",
        "cursor": "Cursor",
        "chatgpt": "ChatGPT",
        "gemini": "Gemini",
        "deepseek": "DeepSeek",
    }
    buttons = [
        InlineKeyboardButton(
            text=name,
            callback_data=f"promptchat:ai:{code}",
        )
        for code, name in models.items()
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons[index:index + 2]
            for index in range(0, len(buttons), 2)
        ]
    )


def news_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "🔥 Попробовать"
                        if language == "ru"
                        else "🔥 Try it"
                    ),
                    callback_data="nav:menu",
                ),
                InlineKeyboardButton(
                    text="⭐ Premium",
                    callback_data="nav:premium",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💬 Отзыв" if language == "ru" else "💬 Feedback",
                    callback_data="news:feedback",
                )
            ],
        ]
    )
