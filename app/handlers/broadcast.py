from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.broadcast import deliver_broadcast
from app.catalog import tr
from app.config import Settings
from app.database import Database


router = Router(name="broadcast")
ACCESS_DENIED = "⛔ У вас нет доступа."


class BroadcastFlow(StatesGroup):
    choosing_audience = State()
    waiting_for_message = State()
    waiting_for_confirmation = State()


def _is_admin(user_id: int | None, settings: Settings) -> bool:
    return user_id is not None and user_id in settings.admin_ids


def audience_keyboard(language: str) -> InlineKeyboardMarkup:
    labels = {
        "all": ("📢 Всем пользователям", "📢 All users"),
        "free": ("🆓 Free", "🆓 Free"),
        "paid": ("⭐ Pro + Premium", "⭐ Pro + Premium"),
        "premium": ("👑 Только Premium", "👑 Premium only"),
    }
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=value[1] if language == "en" else value[0],
                    callback_data=f"broadcast:audience:{key}",
                )
            ]
            for key, value in labels.items()
        ]
    )


def confirmation_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить" if language == "ru" else "✅ Send",
                    callback_data="broadcast:confirm",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена" if language == "ru" else "❌ Cancel",
                    callback_data="broadcast:cancel",
                ),
            ]
        ]
    )


async def start_broadcast(
    message: Message,
    db: Database,
    state: FSMContext,
    telegram_id: int,
) -> None:
    user = await db.get_user_by_telegram_id(telegram_id)
    language = user.language if user and user.language else "ru"
    await state.clear()
    await state.set_state(BroadcastFlow.choosing_audience)
    await state.update_data(broadcast_language=language)
    await message.answer(
        tr(
            language,
            "📣 Новая рассылка\n\nВыберите аудиторию:",
            "📣 New broadcast\n\nChoose an audience:",
        ),
        reply_markup=audience_keyboard(language),
    )


@router.message(Command("broadcast"))
async def broadcast_command(
    message: Message,
    db: Database,
    settings: Settings,
    state: FSMContext,
) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id, settings):
        await message.answer(ACCESS_DENIED)
        return
    await start_broadcast(message, db, state, user_id)


@router.callback_query(F.data.startswith("broadcast:audience:"))
async def choose_audience(
    callback: CallbackQuery,
    db: Database,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED, show_alert=True)
        return
    audience = (callback.data or "").rsplit(":", 1)[-1]
    if audience not in {"all", "free", "paid", "premium"}:
        await callback.answer("Invalid audience", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user and user.language else "ru"
    await state.set_state(BroadcastFlow.waiting_for_message)
    await state.update_data(
        audience=audience,
        broadcast_language=language,
    )
    if isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                language,
                "Отправьте текст, фото, документ или видео для рассылки.",
                "Send text, a photo, document or video for the broadcast.",
            )
        )
    await callback.answer()


def _broadcast_text(message: Message) -> str:
    return (message.text or message.caption or "").strip()


@router.message(BroadcastFlow.waiting_for_message)
async def capture_broadcast(
    message: Message,
    bot: Bot,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None, settings):
        await message.answer(ACCESS_DENIED)
        return
    supported = bool(
        message.text
        or message.photo
        or message.document
        or message.video
    )
    data = await state.get_data()
    language = data.get("broadcast_language", "ru")
    if not supported:
        await message.answer(
            tr(
                language,
                "Поддерживаются текст, фото, документ и видео.",
                "Text, photos, documents and videos are supported.",
            )
        )
        return
    await state.update_data(
        source_chat_id=message.chat.id,
        source_message_id=message.message_id,
        news_text=_broadcast_text(message),
    )
    await bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await state.set_state(BroadcastFlow.waiting_for_confirmation)
    await message.answer(
        tr(
            language,
            "👆 Предпросмотр рассылки\n\nОтправить сообщение?",
            "👆 Broadcast preview\n\nSend this message?",
        ),
        reply_markup=confirmation_keyboard(language),
    )


@router.callback_query(F.data == "broadcast:cancel")
async def cancel_broadcast(
    callback: CallbackQuery,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED, show_alert=True)
        return
    data = await state.get_data()
    language = data.get("broadcast_language", "ru")
    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            tr(language, "❌ Рассылка отменена.", "❌ Broadcast cancelled.")
        )
    await callback.answer()


@router.callback_query(F.data == "broadcast:confirm")
async def confirm_broadcast(
    callback: CallbackQuery,
    bot: Bot,
    db: Database,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED, show_alert=True)
        return
    data = await state.get_data()
    required = {"audience", "source_chat_id", "source_message_id"}
    if not required.issubset(data):
        await callback.answer("Broadcast data is missing", show_alert=True)
        return
    language = data.get("broadcast_language", "ru")
    await callback.answer()
    if isinstance(callback.message, Message):
        status = await callback.message.answer(
            tr(
                language,
                "⏳ Отправляю рассылку…",
                "⏳ Sending broadcast…",
            )
        )
    else:
        return
    result = await deliver_broadcast(
        bot,
        db,
        data["audience"],
        int(data["source_chat_id"]),
        int(data["source_message_id"]),
    )
    raw_text = str(data.get("news_text") or "").strip()
    title = next(
        (line.strip() for line in raw_text.splitlines() if line.strip()),
        tr(language, "Обновление PromptCraft AI", "PromptCraft AI update"),
    )
    await db.save_news(title, raw_text or title, language)
    await state.clear()
    await status.edit_text(
        tr(
            language,
            "✅ Рассылка завершена\n\n"
            f"📨 Отправлено: {result.sent}\n"
            f"⚠️ Ошибок: {result.errors}\n"
            f"🚫 Заблокировали бота: {result.blocked}\n"
            f"👥 Всего получателей: {result.total}",
            "✅ Broadcast completed\n\n"
            f"📨 Sent: {result.sent}\n"
            f"⚠️ Errors: {result.errors}\n"
            f"🚫 Bot blocked: {result.blocked}\n"
            f"👥 Total recipients: {result.total}",
        )
    )
