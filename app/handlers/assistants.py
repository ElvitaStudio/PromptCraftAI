from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.assistant_keyboards import (
    assistants_menu_keyboard,
    premium_plus_upgrade_keyboard,
)
from app.keyboards import premium_keyboard
from app.assistant_workspace import assistant_upgrade_text
from app.catalog import tr
from app.config import Settings
from app.database import Database
from app.plans import (
    PREMIUM_PLUS_PRICE_STARS,
    has_assistant_access,
)
from app.trial import trial_status_text


router = Router(name="assistants")


@router.callback_query(F.data == "assistants:menu")
async def assistants_menu(
    callback: CallbackQuery,
    db: Database,
    settings: Settings | None = None,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user and user.language else "ru"
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    is_admin = bool(
        settings is not None
        and callback.from_user.id in settings.admin_ids
    )
    if not user or (
        not has_assistant_access(user.plan, user.trial_active)
        and not is_admin
    ):
        text = (
            trial_status_text(user, language)
            if user and user.trial_granted
            else assistant_upgrade_text(language)
        )
        await callback.message.answer(
            text,
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
                "Срок подписки: 30 дней.",
                "💎 Premium Plus\n\n"
                "• GPT Assistant\n"
                "• Claude Assistant\n"
                "• Separate memory and history\n"
                "• Search and save chats\n\n"
                f"Price: {PREMIUM_PLUS_PRICE_STARS} Stars.\n"
                "Subscription period: 30 days.",
            ),
            reply_markup=premium_keyboard(language),
        )
    await callback.answer()
