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
            )
        ],
        [
            InlineKeyboardButton(
                text=(
                    "🔧 Улучшить мой промпт"
                    if language == "ru"
                    else "🔧 Optimize My Prompt"
                ),
                callback_data="workflow:optimize",
            )
        ],
        [
            InlineKeyboardButton(
                text=(
                    "🔥 Промпт дня"
                    if language == "ru"
                    else "🔥 Prompt of the Day"
                ),
                callback_data="nav:daily",
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Шаблоны" if language == "ru" else "📚 Templates",
                callback_data="nav:templates",
            ),
            InlineKeyboardButton(
                text="⭐ Избранное" if language == "ru" else "⭐ Favorites",
                callback_data="nav:favorites",
            ),
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
    items = list(RESPONSE_STYLES.items())
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


def premium_keyboard() -> InlineKeyboardMarkup:
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
                    text="🎁 Invite a friend",
                    callback_data="payment:invite",
                )
            ],
        ]
    )
