from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.catalog import tr
from app.database import Database
from app.keyboards import news_keyboard
from app.presentation import split_text


router = Router(name="news")


async def show_news(
    message: Message,
    db: Database,
    telegram_id: int,
) -> None:
    user = await db.get_user_by_telegram_id(telegram_id)
    if not user:
        return
    language = user.language or "ru"
    items = await db.get_news(language, 20)
    if not items:
        await message.answer(
            tr(
                language,
                "📰 Новостей пока нет.",
                "📰 No news yet.",
            )
        )
        return
    await message.answer(
        tr(
            language,
            "📰 Новости PromptCraft AI",
            "📰 PromptCraft AI News",
        )
    )
    for item in items:
        chunks = split_text(
            f"<b>{escape(item.title)}</b>\n\n{escape(item.text)}"
        )
        for index, chunk in enumerate(chunks):
            await message.answer(
                chunk,
                parse_mode="HTML",
                reply_markup=(
                    news_keyboard(language)
                    if index == len(chunks) - 1
                    else None
                ),
            )


@router.message(Command("news"))
async def news_command(message: Message, db: Database) -> None:
    if message.from_user:
        await show_news(message, db, message.from_user.id)


@router.callback_query(F.data == "news:feedback")
async def news_feedback(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user and user.language else "ru"
    if isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                language,
                "💬 Спасибо! Отправьте ваш отзыв обычным сообщением "
                "или воспользуйтесь /paysupport для связи.",
                "💬 Thank you! Send your feedback as a regular message "
                "or use /paysupport to contact us.",
            )
        )
    await callback.answer()
