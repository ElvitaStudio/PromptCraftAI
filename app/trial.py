from __future__ import annotations

from datetime import datetime, timezone

from app.catalog import tr
from app.database import User
from app.plans import TRIAL_AI_REQUEST_LIMIT


def new_user_trial_message(language: str) -> str:
    return tr(
        language,
        "🎉 Добро пожаловать в PromptCraftAI!\n\n"
        "Вам открыт бесплатный Premium Plus Trial.\n\n"
        "Срок действия: 24 часа.\n\n"
        "Доступно 15 AI-запросов.\n\n"
        "Попробуйте все возможности PromptCraftAI бесплатно.",
        "🎉 Welcome to PromptCraftAI!\n\n"
        "Your Premium Plus Trial has been activated.\n\n"
        "Duration: 24 hours.\n\n"
        "15 AI requests are available.\n\n"
        "Enjoy all PromptCraftAI features for free.",
    )


def existing_user_trial_message(language: str) -> str:
    return tr(
        language,
        "🎁 В честь большого обновления PromptCraftAI вам открыт "
        "Premium Plus Trial на 24 часа.\n\n"
        "Доступно 15 AI-запросов.",
        "🎁 As part of the major PromptCraftAI update, your Premium Plus "
        "Trial has been activated for 24 hours.\n\n"
        "15 AI requests are available.",
    )


def trial_status_text(user: User, language: str) -> str:
    if user.trial_active and user.trial_expires_at:
        expires = datetime.fromisoformat(user.trial_expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        seconds = max(
            0,
            int((expires - datetime.now(timezone.utc)).total_seconds()),
        )
        hours, remainder = divmod(seconds, 3600)
        minutes = remainder // 60
        return tr(
            language,
            "🟢 Trial активен\n\n"
            f"Осталось: {user.trial_remaining} / "
            f"{TRIAL_AI_REQUEST_LIMIT} запросов\n\n"
            f"До окончания: {hours}ч {minutes}м",
            "🟢 Trial active\n\n"
            f"Remaining: {user.trial_remaining} / "
            f"{TRIAL_AI_REQUEST_LIMIT} requests\n\n"
            f"Time left: {hours}h {minutes}m",
        )
    if user.trial_granted:
        return tr(
            language,
            "🔒 Trial завершён.\n\n"
            "Для продолжения оформите Premium Plus.",
            "🔒 Trial ended.\n\n"
            "Upgrade to Premium Plus to continue.",
        )
    return ""


def infer_telegram_language(telegram_user) -> str:
    code = getattr(telegram_user, "language_code", "") or ""
    return "ru" if code.lower().startswith("ru") else "en"
