from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.catalog import AI_MODELS, CATEGORIES, tr
from app.database import Database, PromptRecord
from app.exports import prompt_markdown, prompt_txt
from app.keyboards import history_list_keyboard, history_prompt_keyboard
from app.presentation import split_text


router = Router(name="history")
EXTRA_AI_NAMES = {"deepseek": "DeepSeek"}


def _date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone().strftime("%d.%m.%Y %H:%M")


def _list_title(record: PromptRecord, language: str) -> str:
    ai_name = AI_MODELS.get(
        record.target_ai,
        EXTRA_AI_NAMES.get(record.target_ai, record.target_ai.title()),
    )
    source = " ".join(record.source_text.split())
    if len(source) > 35:
        source = source[:32].rstrip() + "..."
    return f"{ai_name} · {source or tr(language, 'Промпт', 'Prompt')}"


def history_card(record: PromptRecord, language: str) -> str:
    category = CATEGORIES.get(record.category, {}).get(
        language,
        record.category,
    )
    ai_name = AI_MODELS.get(
        record.target_ai,
        EXTRA_AI_NAMES.get(record.target_ai, record.target_ai.title()),
    )
    source = record.source_text.strip()
    prompt = record.prompt_text.strip()
    if len(source) > 900:
        source = source[:897].rstrip() + "..."
    if len(prompt) > 2200:
        prompt = prompt[:2197].rstrip() + "..."
    return tr(
        language,
        "📜 Промпт из истории\n\n"
        f"📅 {_date(record.created_at)}\n"
        f"🧩 Категория: {category}\n"
        f"🤖 AI: {ai_name}\n"
        f"🌐 Язык: {record.language.upper()}\n\n"
        f"📥 Исходный запрос\n{source}\n\n"
        f"✨ Итоговый промпт\n{prompt}",
        "📜 Prompt history item\n\n"
        f"📅 {_date(record.created_at)}\n"
        f"🧩 Category: {category}\n"
        f"🤖 AI: {ai_name}\n"
        f"🌐 Language: {record.language.upper()}\n\n"
        f"📥 Original request\n{source}\n\n"
        f"✨ Final prompt\n{prompt}",
    )


async def show_history_page(
    message: Message,
    db: Database,
    telegram_id: int,
    page: int = 0,
) -> None:
    user = await db.get_user_by_telegram_id(telegram_id)
    if not user:
        return
    language = user.language or "ru"
    history = await db.get_prompt_history_page(user, page)
    if not history.prompts:
        await message.answer(
            tr(
                language,
                "📭 История пока пустая. Создайте первый промпт.",
                "📭 History is empty. Create your first prompt.",
            )
        )
        return
    await message.answer(
        tr(
            language,
            f"📜 История промптов\n\nСтраница "
            f"{history.page + 1}/{history.total_pages}",
            f"📜 Prompt history\n\nPage "
            f"{history.page + 1}/{history.total_pages}",
        ),
        reply_markup=history_list_keyboard(
            [
                (record.id, _list_title(record, language))
                for record in history.prompts
            ],
            history.page,
            history.total_pages,
            language,
        ),
    )


@router.callback_query(F.data == "nav:history")
async def history_menu(callback: CallbackQuery, db: Database) -> None:
    if isinstance(callback.message, Message):
        await show_history_page(
            callback.message,
            db,
            callback.from_user.id,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("history:page:"))
async def history_page(callback: CallbackQuery, db: Database) -> None:
    try:
        page = int((callback.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer("Invalid page", show_alert=True)
        return
    if isinstance(callback.message, Message):
        await show_history_page(
            callback.message,
            db,
            callback.from_user.id,
            page,
        )
    await callback.answer()


@router.callback_query(F.data == "history:noop")
async def history_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("history:open:"))
async def open_history_prompt(callback: CallbackQuery, db: Database) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await callback.answer("Invalid prompt", show_alert=True)
        return
    try:
        prompt_id, page = int(parts[2]), int(parts[3])
    except ValueError:
        await callback.answer("Invalid prompt", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not isinstance(callback.message, Message):
        await callback.answer()
        return
    record = await db.get_prompt(prompt_id, user.id)
    if not record:
        await callback.answer(
            tr(user.language or "ru", "Промпт не найден", "Prompt not found"),
            show_alert=True,
        )
        return
    chunks = split_text(history_card(record, user.language or "ru"))
    for index, chunk in enumerate(chunks):
        await callback.message.answer(
            chunk,
            reply_markup=(
                history_prompt_keyboard(
                    record.id,
                    page,
                    user.language or "ru",
                )
                if index == len(chunks) - 1
                else None
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("history:reuse:"))
async def reuse_history_prompt(callback: CallbackQuery, db: Database) -> None:
    try:
        prompt_id = int((callback.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer("Invalid prompt", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not isinstance(callback.message, Message):
        await callback.answer()
        return
    record = await db.get_prompt(prompt_id, user.id)
    if not record:
        await callback.answer("Prompt not found", show_alert=True)
        return
    await callback.message.answer(record.prompt_text)
    await callback.answer(
        tr(
            user.language or "ru",
            "Промпт отправлен для повторного использования",
            "Prompt sent for reuse",
        )
    )


@router.callback_query(F.data.startswith("history:favorite:"))
async def favorite_history_prompt(callback: CallbackQuery, db: Database) -> None:
    try:
        prompt_id = int((callback.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer("Invalid prompt", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    record = await db.get_prompt(prompt_id, user.id)
    if not record:
        await callback.answer("Prompt not found", show_alert=True)
        return
    title = next(
        (line.strip() for line in record.prompt_text.splitlines() if line.strip()),
        "Prompt",
    )
    added = await db.add_favorite(user.id, record.id, title)
    await callback.answer(
        tr(
            user.language or "ru",
            "Добавлено в избранное" if added else "Уже в избранном",
            "Added to favorites" if added else "Already in favorites",
        ),
        show_alert=True,
    )


@router.callback_query(F.data.startswith("history:export:"))
async def export_history_prompt(callback: CallbackQuery, db: Database) -> None:
    try:
        prompt_id = int((callback.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer("Invalid prompt", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not isinstance(callback.message, Message):
        await callback.answer()
        return
    record = await db.get_prompt(prompt_id, user.id)
    if not record:
        await callback.answer("Prompt not found", show_alert=True)
        return
    markdown = user.export_format == "markdown"
    content = prompt_markdown(record) if markdown else prompt_txt(record)
    extension = "md" if markdown else "txt"
    await callback.message.answer_document(
        BufferedInputFile(
            content,
            filename=f"promptcraft-{record.id}.{extension}",
        )
    )
    await callback.answer()
