from __future__ import annotations

from app.database import AIRequestReservation, Database, User


async def reserve_model_request(
    db: Database,
    user: User,
) -> AIRequestReservation:
    reserve = getattr(db, "reserve_ai_request", None)
    if reserve is not None:
        return await reserve(user)
    legacy = getattr(db, "reserve_request", None)
    if legacy is not None:
        allowed = await legacy(user)
        return AIRequestReservation(
            allowed,
            "plan" if allowed else None,
        )
    return AIRequestReservation(True, None)


async def release_model_request(
    db: Database,
    user: User,
    reservation: AIRequestReservation,
) -> None:
    release = getattr(db, "release_ai_request", None)
    if release is not None:
        await release(user, reservation)
        return
    legacy = getattr(db, "release_request", None)
    if legacy is not None and reservation.source == "plan":
        await legacy(user)
