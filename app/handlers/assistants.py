from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.assistant_keyboards import (
    assistants_menu_keyboard,
    premium_plus_upgrade_keyboard,
)
from app.assistant_workspace import assistant_upgrade_text
from app.catalog import tr
from app.database import Database
from app.plans import (
    PREMIUM_PLUS_PRICE_STARS,
    has_assistant_access,
)


router = Router(name="assistants")


@router.callback_query(F.data == "assistants:menu")
async def assistants_menu(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user and user.language else "ru"
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    if not user or not has_assistant_access(user.plan):
        await callback.message.answer(
            assistant_upgrade_text(language),
            reply_markup=premium_plus_upgrade_keyboard(language),
        )
        await callback.answer()
        return
    await callback.message.answer(
        tr(
            language,
            "🤖 AI Assistants\n\nВыберите ассистента:",
            "🤖 AI Assistants\n\nChoose an assistant:",
        ),
        reply_markup=assistants_menu_keyboard(language),
    )
    await callback.answer()


@router.callback_query(F.data == "premium_plus:info")
async def premium_plus_info(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user and user.language else "ru"
    if isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                language,
                "💎 Premium Plus\n\n"
                "• GPT Assistant\n"
                "• Claude Assistant\n"
                "• Раздельная история и память\n"
                "• Поиск и сохранение чатов\n\n"
                f"Стоимость: {PREMIUM_PLUS_PRICE_STARS} Stars.\n"
                "Оплата будет подключена позже.",
                "💎 Premium Plus\n\n"
                "• GPT Assistant\n"
                "• Claude Assistant\n"
                "• Separate history and memory\n"
                "• Chat search and saved conversations\n\n"
                f"Price: {PREMIUM_PLUS_PRICE_STARS} Stars.\n"
                "Payments will be connected later.",
            )
        )
    await callback.answer()
