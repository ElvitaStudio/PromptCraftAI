from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.admin import user_button_text
from app.database import AdminUser, AdminUserPage


def _button(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=f"admin:{data}")


def dashboard_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    is_en = language == "en"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_button("👥 Users" if is_en else "👥 Пользователи", "users:0")],
            [_button("🔎 Search" if is_en else "🔎 Поиск", "search")],
            [_button("🎁 Referrals" if is_en else "🎁 Рефералы", "referrals")],
            [_button("📣 Broadcast" if is_en else "📣 Рассылка", "broadcast")],
            [_button("📰 News" if is_en else "📰 Новости", "news")],
            [_button("⬅️ Close" if is_en else "⬅️ Закрыть", "close")],
        ]
    )


def users_keyboard(
    page: AdminUserPage,
    search: str | None = None,
) -> InlineKeyboardMarkup:
    search_token = search or "-"
    rows = [
        [
            _button(
                user_button_text(page.page * 10 + index, user),
                f"user:{user.user_id}:{page.page}:{search_token}",
            )
        ]
        for index, user in enumerate(page.users, 1)
    ]
    nav = []
    if page.page > 0:
        nav.append(_button("◀️", f"users:{page.page - 1}:{search_token}"))
    if page.page + 1 < page.total_pages:
        nav.append(_button("➡️", f"users:{page.page + 1}:{search_token}"))
    if nav:
        rows.append(nav)
    rows.append([_button("⬅️ Назад", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_card_keyboard(
    user: AdminUser,
    page: int,
    search: str | None = None,
) -> InlineKeyboardMarkup:
    token = search or "-"
    suffix = f"{user.user_id}:{page}:{token}"
    block_text = "✅ Разблокировать" if user.is_blocked else "🚫 Заблокировать"
    block_action = "unblock" if user.is_blocked else "block"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_button("🎁 +3 дня Premium", f"grant:extend:{suffix}")],
            [_button("👑 Выдать Premium", f"grant:premium:{suffix}")],
            [_button("⭐ Выдать Pro", f"grant:pro:{suffix}")],
            [_button("🆓 Сбросить Free", f"grant:free:{suffix}")],
            [_button(block_text, f"{block_action}:{suffix}")],
            [_button("⬅️ К списку", f"users:{page}:{token}")],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_button("⬅️ Назад", "home")]]
    )
