from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.catalog import LANGUAGES, tr
from app.database import Database
from app.keyboards import categories_keyboard


router = Router(name="language")


@router.callback_query(F.data.startswith("language:"))
async def select_language(
    callback: CallbackQuery,
    db: Database,
) -> None:
    language = (callback.data or "").split(":", 1)[-1]
    if language not in LANGUAGES:
        await callback.answer("Invalid language", show_alert=True)
        return
    await db.set_language(callback.from_user.id, language)
    if isinstance(callback.message, Message):
        await callback.message.answer(
            tr(
                language,
                "✅ Язык сохранён.\n\n🧩 Выберите категорию:",
                "✅ Language saved.\n\n🧩 Choose a category:",
            ),
            reply_markup=categories_keyboard(language),
        )
    await callback.answer()
