from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from app.database import User
from app.middlewares import UserProfileMiddleware


class MiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def test_non_text_message_does_not_crash(self) -> None:
        middleware = UserProfileMiddleware()
        handler = AsyncMock(return_value="ok")
        db = SimpleNamespace(
            upsert_user=AsyncMock(
                return_value=User(1, 42, "free")
            )
        )
        event = SimpleNamespace(
            text=None,
            from_user=SimpleNamespace(
                id=42,
                is_bot=False,
                username="user",
                first_name="User",
                last_name=None,
            ),
        )
        self.assertEqual(
            await middleware(handler, event, {"db": db}),
            "ok",
        )

    async def test_start_is_not_pre_registered(self) -> None:
        middleware = UserProfileMiddleware()
        db = SimpleNamespace(upsert_user=AsyncMock())
        event = SimpleNamespace(
            text="/start ref_1",
            from_user=SimpleNamespace(id=42, is_bot=False),
        )
        await middleware(AsyncMock(), event, {"db": db})
        db.upsert_user.assert_not_awaited()
