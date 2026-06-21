from __future__ import annotations

from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.assistant_keyboards import (
    ASSISTANT_LABELS,
    assistant_chat_keyboard,
    assistant_chats_keyboard,
    premium_plus_upgrade_keyboard,
)
from app.catalog import tr
from app.database import AssistantMessage, Database
from app.plans import has_assistant_access
from app.presentation import split_text


def assistant_upgrade_text(language: str) -> str:
    return tr(
        language,
        "💎 Premium Plus требуется для AI Assistants.\n\n"
        "Доступны GPT, Claude и Gemini с отдельной историей, "
        "контекстом, поиском и сохранением диалогов.",
        "💎 Premium Plus is required for AI Assistants.\n\n"
        "GPT, Claude and Gemini include separate history, context, "
        "search and saved conversations.",
    )


def _history_text(
    assistant: str,
    title: str,
    messages: list[AssistantMessage],
    language: str,
) -> str:
    lines = [f"{ASSISTANT_LABELS[assistant]} · {title}"]
    if not messages:
        lines.extend(
            [
                "",
                tr(
                    language,
                    "История пуста. Отправьте первое сообщение.",
                    "The chat is empty. Send the first message.",
                ),
            ]
        )
    else:
        for item in messages[-20:]:
            role = (
                ("Вы" if language == "ru" else "You")
                if item.role == "user"
                else ASSISTANT_LABELS[assistant]
            )
            content = item.content
            if len(content) > 700:
                content = content[:697].rstrip() + "..."
            lines.extend(["", f"{role}:", content])
    return "\n".join(lines)


async def ensure_assistant_access(
    message: Message,
    db: Database,
    telegram_id: int,
) -> tuple[Any | None, str]:
    user = await db.get_user_by_telegram_id(telegram_id)
    language = user.language if user and user.language else "ru"
    if not user or not has_assistant_access(user.plan):
        await message.answer(
            assistant_upgrade_text(language),
            reply_markup=premium_plus_upgrade_keyboard(language),
        )
        return None, language
    return user, language


async def show_assistant_chats(
    message: Message,
    db: Database,
    telegram_id: int,
    assistant: str,
    search: str | None = None,
) -> None:
    user, language = await ensure_assistant_access(message, db, telegram_id)
    if not user:
        return
    chats = await db.get_assistant_chats(user.id, assistant, search)
    title = ASSISTANT_LABELS[assistant]
    suffix = (
        tr(language, f"\n🔎 Поиск: {search}", f"\n🔎 Search: {search}")
        if search
        else ""
    )
    empty = (
        tr(
            language,
            "\n\nЧатов пока нет.",
            "\n\nNo chats yet.",
        )
        if not chats
        else ""
    )
    await message.answer(
        f"{title}{suffix}{empty}",
        reply_markup=assistant_chats_keyboard(assistant, chats, language),
    )


async def start_new_assistant_chat(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    assistant: str,
    waiting_state,
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    user, language = await ensure_assistant_access(
        callback.message,
        db,
        callback.from_user.id,
    )
    if not user:
        await callback.answer()
        return
    title = tr(language, "Новый чат", "New chat")
    chat = await db.create_assistant_chat(user.id, assistant, title)
    await state.set_state(waiting_state)
    await state.update_data(
        assistant_chat_id=chat.id,
        active_assistant=assistant,
    )
    await callback.message.answer(
        tr(
            language,
            f"{ASSISTANT_LABELS[assistant]} · Новый чат\n\n"
            "Отправьте первое сообщение.",
            f"{ASSISTANT_LABELS[assistant]} · New chat\n\n"
            "Send your first message.",
        ),
        reply_markup=assistant_chat_keyboard(assistant, chat.id, language),
    )
    await callback.answer()


async def open_assistant_chat(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    assistant: str,
    chat_id: int,
    waiting_state,
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    user, language = await ensure_assistant_access(
        callback.message,
        db,
        callback.from_user.id,
    )
    if not user:
        await callback.answer()
        return
    chat = await db.get_assistant_chat(chat_id, user.id, assistant)
    if chat is None:
        await callback.answer(
            tr(language, "Чат не найден", "Chat not found"),
            show_alert=True,
        )
        return
    messages = await db.get_assistant_messages(
        chat.id,
        user.id,
        assistant,
    )
    await state.set_state(waiting_state)
    await state.update_data(
        assistant_chat_id=chat.id,
        active_assistant=assistant,
    )
    chunks = split_text(
        _history_text(assistant, chat.title, messages, language)
    )
    for index, chunk in enumerate(chunks):
        await callback.message.answer(
            chunk,
            reply_markup=(
                assistant_chat_keyboard(assistant, chat.id, language)
                if index == len(chunks) - 1
                else None
            ),
        )
    await callback.answer()


async def delete_assistant_chat(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    assistant: str,
    chat_id: int,
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    user, language = await ensure_assistant_access(
        callback.message,
        db,
        callback.from_user.id,
    )
    if not user:
        await callback.answer()
        return
    deleted = await db.delete_assistant_chat(chat_id, user.id, assistant)
    await state.clear()
    await callback.answer(
        tr(
            language,
            "Чат удалён" if deleted else "Чат не найден",
            "Chat deleted" if deleted else "Chat not found",
        ),
        show_alert=True,
    )
    await show_assistant_chats(
        callback.message,
        db,
        callback.from_user.id,
        assistant,
    )


async def begin_assistant_search(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    assistant: str,
    search_state,
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    user, language = await ensure_assistant_access(
        callback.message,
        db,
        callback.from_user.id,
    )
    if not user:
        await callback.answer()
        return
    await state.set_state(search_state)
    await state.update_data(active_assistant=assistant)
    await callback.message.answer(
        tr(
            language,
            "🔎 Введите название чата или текст сообщения:",
            "🔎 Enter a chat title or message text:",
        )
    )
    await callback.answer()


async def handle_assistant_search(
    message: Message,
    db: Database,
    state: FSMContext,
    assistant: str,
) -> None:
    if not message.from_user or not message.text:
        return
    await show_assistant_chats(
        message,
        db,
        message.from_user.id,
        assistant,
        message.text,
    )
    await state.clear()


async def handle_assistant_message(
    message: Message,
    db: Database,
    state: FSMContext,
    assistant: str,
    service: Any,
) -> None:
    if not message.from_user or not message.text:
        return
    user, language = await ensure_assistant_access(
        message,
        db,
        message.from_user.id,
    )
    if not user:
        await state.clear()
        return
    data = await state.get_data()
    if (
        data.get("active_assistant") != assistant
        or not data.get("assistant_chat_id")
    ):
        await state.clear()
        await show_assistant_chats(
            message,
            db,
            message.from_user.id,
            assistant,
        )
        return
    chat_id = int(data["assistant_chat_id"])
    previous = await db.get_assistant_messages(
        chat_id,
        user.id,
        assistant,
    )
    if not previous:
        await db.rename_assistant_chat(
            chat_id,
            user.id,
            assistant,
            message.text,
        )
    await db.add_assistant_message(
        chat_id,
        user.id,
        assistant,
        "user",
        message.text,
    )
    context = await db.get_assistant_messages(
        chat_id,
        user.id,
        assistant,
    )
    try:
        response = await service.reply(
            [
                {"role": item.role, "content": item.content}
                for item in context
            ],
            language,
        )
    except Exception:
        await message.answer(
            tr(
                language,
                "Не удалось получить ответ ассистента. "
                "Ваше сообщение сохранено, попробуйте позже.",
                "The assistant could not respond. "
                "Your message was saved; try again later.",
            ),
            reply_markup=assistant_chat_keyboard(
                assistant,
                chat_id,
                language,
            ),
        )
        return
    await db.add_assistant_message(
        chat_id,
        user.id,
        assistant,
        "assistant",
        response,
    )
    await message.answer(
        response,
        reply_markup=assistant_chat_keyboard(
            assistant,
            chat_id,
            language,
        ),
    )
