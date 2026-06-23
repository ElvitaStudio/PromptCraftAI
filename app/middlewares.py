from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.database import Database
from app.trial import (
    existing_user_trial_message,
    infer_telegram_language,
)


def telegram_profile(message: Message) -> tuple[
    int, str | None, str | None, str | None, str | None
]:
    if message.from_user is None:
        raise ValueError("Message has no sender")
    user = message.from_user
    first = getattr(user, "first_name", None)
    last = getattr(user, "last_name", None)
    full = " ".join(part for part in (first, last) if part) or None
    return user.id, getattr(user, "username", None), first, last, full


class UserProfileMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        parts = (event.text or "").split(maxsplit=1)
        command = parts[0].split("@", 1)[0] if parts else ""
        if (
            event.from_user is not None
            and not event.from_user.is_bot
            and command != "/start"
        ):
            db: Database | None = data.get("db")
            if db:
                data["profile_user"] = await db.upsert_user(
                    *telegram_profile(event)
                )
                activate = getattr(db, "activate_trial_once", None)
                if activate is not None:
                    activation = await activate(event.from_user.id)
                    if (
                        activation is not None
                        and activation.notification_required
                    ):
                        language = (
                            activation.user.language
                            or infer_telegram_language(event.from_user)
                        )
                        await event.answer(
                            existing_user_trial_message(language)
                        )
        return await handler(event, data)


class TrialCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        db: Database | None = data.get("db")
        activate = getattr(db, "activate_trial_once", None) if db else None
        if activate is not None:
            activation = await activate(event.from_user.id)
            if (
                activation is not None
                and activation.notification_required
                and isinstance(event.message, Message)
            ):
                language = (
                    activation.user.language
                    or infer_telegram_language(event.from_user)
                )
                await event.message.answer(
                    existing_user_trial_message(language)
                )
        return await handler(event, data)
