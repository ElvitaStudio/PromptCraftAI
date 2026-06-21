from datetime import datetime

from app.database import (
    AdminReferralReport,
    AdminStatistics,
    AdminUser,
    AdminUserPage,
)
from app.presentation import split_text


def _date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value


def dashboard_text(stats: AdminStatistics) -> str:
    return (
        "👑 PromptCraft AI Admin\n\n"
        f"👥 Пользователей: {stats.total_users}\n"
        f"🆓 Free: {stats.free_users}\n"
        f"⭐ Pro: {stats.pro_users}\n"
        f"👑 Premium: {stats.premium_users}\n"
        f"💎 Premium Plus: {stats.premium_plus_users}\n"
        f"🆕 Новых за 24 часа: {stats.new_users_24h}\n"
        f"💫 Доход: {stats.revenue_stars} Stars\n"
        f"⭐ Продаж Pro: {stats.pro_sales}\n"
        f"👑 Продаж Premium: {stats.premium_sales}\n"
        f"🧩 Промптов всего: {stats.prompts_total}\n"
        f"📊 Промптов сегодня: {stats.prompts_today}\n\n"
        "Выберите действие:"
    )


def users_page_text(page: AdminUserPage, search: str | None = None) -> str:
    suffix = f"\n🔎 Поиск: {search}" if search else ""
    return (
        f"👥 Пользователи{suffix}\n\n"
        f"Всего: {page.total_users}\n"
        f"Страница: {page.page + 1}/{page.total_pages}"
    )


def user_button_text(index: int, user: AdminUser) -> str:
    username = f" / @{user.username}" if user.username else ""
    blocked = " 🚫" if user.is_blocked else ""
    return f"{index}. {user.display_name}{username}{blocked}"[:64]


def user_card_text(user: AdminUser) -> str:
    username = f"@{user.username}" if user.username else "—"
    plan_name = user.plan.replace("_", " ").title()
    return (
        f"👤 {user.display_name}\n"
        f"🆔 Telegram ID: {user.telegram_id}\n"
        f"📎 Username: {username}"
        f"\n🌐 Язык: {user.language or '—'}\n"
        f"🎖 Тариф: {plan_name}\n"
        f"⏳ Plan until: {_date(user.plan_until)}\n"
        f"🎁 Referral Premium: {_date(user.premium_until)}\n"
        f"🚫 Заблокирован: {'да' if user.is_blocked else 'нет'}\n"
        f"📅 Регистрация: {_date(user.created_at)}\n"
        f"🧩 Запросов сегодня: {user.requests_today}\n"
        f"📚 Промптов всего: {user.prompts_total}\n"
        f"🎁 Пригласил: {user.referrals_count}"
    )


def referral_chunks(report: AdminReferralReport) -> list[str]:
    lines = [
        "🎁 Рефералы",
        f"Всего приглашений: {report.total_referrals}",
        "",
        "🏆 Топ:",
    ]
    for index, item in enumerate(report.top_referrers, 1):
        username = f" (@{item.username})" if item.username else ""
        lines.append(
            f"{index}. {item.display_name}{username} — {item.invited_count}"
        )
    lines.extend(["", "🔗 Кто кого пригласил:"])
    for item in report.referrals:
        lines.append(f"{item.inviter_name} → {item.invited_name}")
    return split_text("\n".join(lines))
