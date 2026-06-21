from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.admin import (
    dashboard_text,
    referral_chunks,
    user_card_text,
    users_page_text,
)
from app.admin_keyboards import (
    back_keyboard,
    dashboard_keyboard,
    user_card_keyboard,
    users_keyboard,
)
from app.config import Settings
from app.database import Database
from app.plans import FREE, PREMIUM, PRO


router = Router(name="admin")
ACCESS_DENIED = "⛔ У вас нет доступа."


class AdminFlow(StatesGroup):
    waiting_for_search = State()


def _is_admin(user_id: int | None, settings: Settings) -> bool:
    return user_id is not None and user_id in settings.admin_ids


@router.message(Command("admin"))
async def admin_command(
    message: Message,
    db: Database,
    settings: Settings,
) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None, settings):
        await message.answer(ACCESS_DENIED)
        return
    user = await db.get_user_by_telegram_id(message.from_user.id)
    language = user.language if user and user.language else "ru"
    stats = await db.get_admin_statistics()
    await message.answer(
        dashboard_text(stats),
        reply_markup=dashboard_keyboard(language),
    )


async def _show_users(
    message: Message,
    db: Database,
    page_number: int,
    search: str | None = None,
) -> None:
    page = await db.get_admin_users_page(page_number, search=search)
    await message.edit_text(
        users_page_text(page, search),
        reply_markup=users_keyboard(page, search),
    )


async def _show_user(
    message: Message,
    db: Database,
    user_id: int,
    page: int,
    search: str | None,
) -> bool:
    user = await db.get_admin_user(user_id)
    if not user:
        return False
    await message.edit_text(
        user_card_text(user),
        reply_markup=user_card_keyboard(user, page, search),
    )
    return True


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback(
    callback: CallbackQuery,
    db: Database,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(ACCESS_DENIED, show_alert=True)
        return
    if not isinstance(callback.message, Message):
        return
    parts = (callback.data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""
    if action == "home":
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        language = user.language if user and user.language else "ru"
        await callback.message.edit_text(
            dashboard_text(await db.get_admin_statistics()),
            reply_markup=dashboard_keyboard(language),
        )
    elif action == "close":
        await callback.message.delete()
    elif action == "search":
        await state.set_state(AdminFlow.waiting_for_search)
        await callback.message.answer("Введите Telegram ID или username:")
    elif action == "referrals":
        chunks = referral_chunks(await db.get_admin_referral_report())
        await callback.message.edit_text(
            chunks[0],
            reply_markup=back_keyboard(),
        )
        for chunk in chunks[1:]:
            await callback.message.answer(chunk)
    elif action == "broadcast":
        from app.handlers.broadcast import start_broadcast

        await start_broadcast(
            callback.message,
            db,
            state,
            callback.from_user.id,
        )
    elif action == "news":
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        language = user.language if user and user.language else "ru"
        items = await db.get_news(language, 20)
        text = "📰 News\n\n" if language == "en" else "📰 Новости\n\n"
        if items:
            text += "\n".join(
                f"{index}. {item.title}"
                for index, item in enumerate(items, 1)
            )
        else:
            text += "No news yet." if language == "en" else "Новостей пока нет."
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard(),
        )
    elif action == "users":
        page = int(parts[2])
        search = parts[3] if len(parts) > 3 and parts[3] != "-" else None
        await _show_users(callback.message, db, page, search)
    elif action == "user":
        user_id, page = int(parts[2]), int(parts[3])
        search = parts[4] if len(parts) > 4 and parts[4] != "-" else None
        await _show_user(callback.message, db, user_id, page, search)
    elif action == "grant":
        plan_action, user_id, page = parts[2], int(parts[3]), int(parts[4])
        search = parts[5] if len(parts) > 5 and parts[5] != "-" else None
        if plan_action == "extend":
            await db.extend_admin_user_premium(user_id, 3)
        else:
            await db.set_admin_user_plan(
                user_id,
                {"free": FREE, "pro": PRO, "premium": PREMIUM}[plan_action],
            )
        await _show_user(callback.message, db, user_id, page, search)
    elif action in {"block", "unblock"}:
        user_id, page = int(parts[2]), int(parts[3])
        search = parts[4] if len(parts) > 4 and parts[4] != "-" else None
        await db.set_user_blocked(user_id, action == "block")
        await _show_user(callback.message, db, user_id, page, search)
    await callback.answer()


@router.message(AdminFlow.waiting_for_search, F.text)
async def admin_search(
    message: Message,
    db: Database,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None, settings):
        return
    page = await db.get_admin_users_page(0, search=message.text)
    await message.answer(
        users_page_text(page, message.text),
        reply_markup=users_keyboard(page, message.text),
    )
    await state.clear()
