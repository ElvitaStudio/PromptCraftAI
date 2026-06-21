from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.database import Database


@dataclass(frozen=True, slots=True)
class BroadcastResult:
    sent: int
    errors: int
    blocked: int
    total: int


async def deliver_broadcast(
    bot: Bot,
    db: Database,
    audience: str,
    source_chat_id: int,
    source_message_id: int,
) -> BroadcastResult:
    recipients = await db.get_broadcast_recipients(audience)
    sent = 0
    errors = 0
    blocked = 0
    for recipient in recipients:
        try:
            await bot.copy_message(
                chat_id=recipient.telegram_id,
                from_chat_id=source_chat_id,
                message_id=source_message_id,
            )
            sent += 1
        except TelegramForbiddenError:
            blocked += 1
            errors += 1
            await db.set_user_blocked_by_telegram_id(
                recipient.telegram_id,
                True,
            )
        except Exception as exc:
            errors += 1
            if "blocked" in str(exc).lower():
                blocked += 1
                await db.set_user_blocked_by_telegram_id(
                    recipient.telegram_id,
                    True,
                )
    return BroadcastResult(
        sent=sent,
        errors=errors,
        blocked=blocked,
        total=len(recipients),
    )
