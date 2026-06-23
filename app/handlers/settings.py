from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.catalog import AI_MODELS, tr
from app.database import Database
from app.keyboards import (
    language_keyboard,
    settings_ai_keyboard,
    settings_difficulty_keyboard,
    settings_export_keyboard,
    settings_keyboard,
    settings_styles_keyboard,
)
from app.plans import has_premium_features
from app.prompt_profiles import DIFFICULTIES, RESPONSE_STYLES


router = Router(name="settings")


def settings_text(user) -> str:
    language = user.language or "ru"
    export_label = "TXT" if user.export_format == "txt" else "Markdown"
    return tr(
        language,
        "⚙️ Настройки\n\n"
        f"🌐 Язык: {'Русский' if language == 'ru' else 'English'}\n"
        f"🎨 Стиль: {RESPONSE_STYLES[user.last_response_style][language]}\n"
        f"🧠 Уровень: {DIFFICULTIES[user.last_difficulty][language]}\n"
        f"🤖 AI по умолчанию: {AI_MODELS[user.last_target_ai]}\n"
        f"📋 Экспорт: {export_label}",
        "⚙️ Settings\n\n"
        f"🌐 Language: {'English' if language == 'en' else 'Русский'}\n"
        f"🎨 Style: {RESPONSE_STYLES[user.last_response_style][language]}\n"
        f"🧠 Level: {DIFFICULTIES[user.last_difficulty][language]}\n"
        f"🤖 Default AI: {AI_MODELS[user.last_target_ai]}\n"
        f"📋 Export: {export_label}",
    )


async def show_settings(message: Message, db: Database, telegram_id: int) -> None:
    user = await db.get_user_by_telegram_id(telegram_id)
    if not user:
        return
    language = user.language or "ru"
    await message.answer(
        settings_text(user),
        reply_markup=settings_keyboard(language),
    )


@router.message(Command("settings"))
async def settings_command(message: Message, db: Database) -> None:
    if message.from_user:
        await show_settings(message, db, message.from_user.id)


@router.callback_query(F.data == "nav:settings")
async def settings_callback(callback: CallbackQuery, db: Database) -> None:
    if isinstance(callback.message, Message):
        await show_settings(callback.message, db, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "settings:language")
async def settings_language(callback: CallbackQuery) -> None:
    if isinstance(callback.message, Message):
        await callback.message.answer(
            "🌐 Выберите язык / Choose your language",
            reply_markup=language_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "settings:style")
async def settings_style(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user and isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                user.language or "ru",
                "🎨 Выберите стиль ответа:",
                "🎨 Choose a response style:",
            ),
            reply_markup=settings_styles_keyboard(user.language or "ru"),
        )
    await callback.answer()


@router.callback_query(F.data == "settings:difficulty")
async def settings_difficulty(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user and isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                user.language or "ru",
                "🧠 Выберите уровень генерации:",
                "🧠 Choose a generation level:",
            ),
            reply_markup=settings_difficulty_keyboard(user.language or "ru"),
        )
    await callback.answer()


@router.callback_query(F.data == "settings:ai")
async def settings_ai(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user and isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                user.language or "ru",
                "🤖 Выберите AI по умолчанию:",
                "🤖 Choose your default AI:",
            ),
            reply_markup=settings_ai_keyboard(user.language or "ru"),
        )
    await callback.answer()


@router.callback_query(F.data == "settings:export")
async def settings_export(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user and isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                user.language or "ru",
                "📋 Выберите формат экспорта:",
                "📋 Choose an export format:",
            ),
            reply_markup=settings_export_keyboard(user.language or "ru"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("pref:"))
async def save_preference(callback: CallbackQuery, db: Database) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Invalid setting", show_alert=True)
        return
    _, kind, value = parts
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    language = user.language or "ru"
    kwargs = {}
    if kind == "style" and value in {
        "professional", "detailed", "concise", "creative"
    }:
        kwargs["response_style"] = value
    elif kind == "difficulty" and value in DIFFICULTIES:
        if value == "expert" and not has_premium_features(
            user.plan, user.trial_active
        ):
            await callback.answer(
                tr(
                    language,
                    "👑 Expert доступен только в Premium. Подробнее: /premium",
                    "👑 Expert is available only with Premium. See /premium",
                ),
                show_alert=True,
            )
            return
        kwargs["difficulty"] = value
    elif kind == "ai" and value in AI_MODELS:
        kwargs["target_ai"] = value
    elif kind == "export" and value in {"txt", "markdown"}:
        kwargs["export_format"] = value
    else:
        await callback.answer("Invalid setting", show_alert=True)
        return
    await db.update_user_preferences(callback.from_user.id, **kwargs)
    await callback.answer(
        tr(language, "✅ Настройка сохранена", "✅ Setting saved"),
        show_alert=True,
    )
    if isinstance(callback.message, Message):
        await show_settings(callback.message, db, callback.from_user.id)
