from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database import AssistantChat


ASSISTANT_LABELS = {
    "gpt": "🟢 GPT",
    "claude": "🟠 Claude",
    "gemini": "🔵 Gemini",
}


def assistants_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"assistant:{assistant}:list",
                )
            ]
            for assistant, label in ASSISTANT_LABELS.items()
        ]
        + [[
            InlineKeyboardButton(
                text="⬅️ Главное меню" if language == "ru" else "⬅️ Main menu",
                callback_data="nav:menu",
            )
        ]]
    )


def assistant_chats_keyboard(
    assistant: str,
    chats: list[AssistantChat],
    language: str,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=chat.title[:60],
                callback_data=f"assistant:{assistant}:open:{chat.id}",
            )
        ]
        for chat in chats
    ]
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="➕ Новый чат" if language == "ru" else "➕ New chat",
                    callback_data=f"assistant:{assistant}:new",
                ),
                InlineKeyboardButton(
                    text="🔎 Поиск" if language == "ru" else "🔎 Search",
                    callback_data=f"assistant:{assistant}:search",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "⬅️ AI Assistants"
                        if language == "en"
                        else "⬅️ AI Assistants"
                    ),
                    callback_data="assistants:menu",
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def assistant_chat_keyboard(
    assistant: str,
    chat_id: int,
    language: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "🗑 Удалить чат"
                        if language == "ru"
                        else "🗑 Delete chat"
                    ),
                    callback_data=f"assistant:{assistant}:delete:{chat_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "⬅️ К чатам"
                        if language == "ru"
                        else "⬅️ Chats"
                    ),
                    callback_data=f"assistant:{assistant}:list",
                )
            ],
        ]
    )


def premium_plus_upgrade_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 Premium Plus",
                    callback_data="premium_plus:info",
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
