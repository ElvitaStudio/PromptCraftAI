from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from app.bot import set_commands
from app.broadcast import BroadcastResult, deliver_broadcast
from app.config import Settings
from app.database import BroadcastRecipient, Database, NewsItem, User
from app.handlers.broadcast import (
    ACCESS_DENIED,
    BroadcastFlow,
    broadcast_command,
    cancel_broadcast,
    capture_broadcast,
    choose_audience,
    confirm_broadcast,
)
from app.handlers.news import news_command
from app.plans import FREE, PREMIUM, PRO


class FakeState:
    def __init__(self, data=None) -> None:
        self.data = dict(data or {})
        self.state = None
        self.cleared = False

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)

    async def get_data(self):
        return dict(self.data)

    async def clear(self) -> None:
        self.data.clear()
        self.cleared = True


def settings(*admin_ids: int) -> Settings:
    return Settings(
        "token",
        "key",
        admin_ids=frozenset(admin_ids),
    )


class BroadcastAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_broadcast_is_admin_only(self) -> None:
        admin_message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="en")
            )
        )
        state = FakeState()
        await broadcast_command(admin_message, db, settings(1), state)
        self.assertEqual(state.state, BroadcastFlow.choosing_audience)
        self.assertIn("Choose an audience", admin_message.answer.await_args.args[0])

    async def test_non_admin_cannot_start_broadcast(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=2),
            answer=AsyncMock(),
        )
        db = SimpleNamespace()
        state = FakeState()
        await broadcast_command(message, db, settings(1), state)
        self.assertEqual(message.answer.await_args.args[0], ACCESS_DENIED)
        self.assertIsNone(state.state)

    async def test_audience_selection_works(self) -> None:
        callback = SimpleNamespace(
            data="broadcast:audience:paid",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, PREMIUM, language="ru")
            )
        )
        state = FakeState()
        with patch("app.handlers.broadcast.Message", SimpleNamespace):
            await choose_audience(
                callback,
                db,
                settings(1),
                state,
            )
        self.assertEqual(state.state, BroadcastFlow.waiting_for_message)
        self.assertEqual(state.data["audience"], "paid")
        self.assertIn(
            "Отправьте текст",
            callback.message.answer.await_args.args[0],
        )


class BroadcastPreviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_supports_media_and_caption(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            text=None,
            caption="Новая функция",
            photo=[SimpleNamespace(file_id="photo")],
            document=None,
            video=None,
            chat=SimpleNamespace(id=100),
            message_id=55,
            answer=AsyncMock(),
        )
        bot = SimpleNamespace(copy_message=AsyncMock())
        state = FakeState(
            {
                "audience": "all",
                "broadcast_language": "ru",
            }
        )
        await capture_broadcast(message, bot, settings(1), state)
        self.assertEqual(
            state.state,
            BroadcastFlow.waiting_for_confirmation,
        )
        self.assertEqual(state.data["news_text"], "Новая функция")
        bot.copy_message.assert_awaited_once_with(
            chat_id=100,
            from_chat_id=100,
            message_id=55,
        )
        self.assertIn("Предпросмотр", message.answer.await_args.args[0])

    async def test_cancel_clears_broadcast(self) -> None:
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        state = FakeState({"broadcast_language": "en"})
        with patch("app.handlers.broadcast.Message", SimpleNamespace):
            await cancel_broadcast(callback, settings(1), state)
        self.assertTrue(state.cleared)
        self.assertIn("cancelled", callback.message.answer.await_args.args[0])

    async def test_confirm_saves_news_and_shows_statistics(self) -> None:
        status = SimpleNamespace(edit_text=AsyncMock())
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock(return_value=status)),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(save_news=AsyncMock(return_value=5))
        state = FakeState(
            {
                "audience": "free",
                "source_chat_id": 100,
                "source_message_id": 55,
                "news_text": "Big update\nDetails",
                "broadcast_language": "en",
            }
        )
        result = BroadcastResult(7, 2, 1, 9)
        with (
            patch("app.handlers.broadcast.Message", SimpleNamespace),
            patch(
                "app.handlers.broadcast.deliver_broadcast",
                AsyncMock(return_value=result),
            ),
        ):
            await confirm_broadcast(
                callback,
                SimpleNamespace(),
                db,
                settings(1),
                state,
            )
        db.save_news.assert_awaited_once_with(
            "Big update",
            "Big update\nDetails",
            "en",
        )
        report = status.edit_text.await_args.args[0]
        self.assertIn("Sent: 7", report)
        self.assertIn("Errors: 2", report)
        self.assertIn("Bot blocked: 1", report)
        self.assertIn("Total recipients: 9", report)
        self.assertTrue(state.cleared)


class BroadcastDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_database_gets_safety_columns_and_news(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.db"
            import aiosqlite

            async with aiosqlite.connect(path) as connection:
                await connection.execute(
                    """
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL UNIQUE,
                        username TEXT, first_name TEXT, last_name TEXT,
                        full_name TEXT, language TEXT,
                        plan TEXT NOT NULL DEFAULT 'free', plan_until TEXT,
                        referred_by INTEGER, premium_until TEXT,
                        created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                    )
                    """
                )
                await connection.commit()
            db = Database(path)
            await db.initialize()
            async with db._connect() as connection:
                user_columns = {
                    row[1]
                    for row in await (
                        await connection.execute("PRAGMA table_info(users)")
                    ).fetchall()
                }
                news_table = await (
                    await connection.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='news'"
                    )
                ).fetchone()
            self.assertIn("is_blocked", user_columns)
            self.assertIn("last_active_at", user_columns)
            self.assertIsNotNone(news_table)

    async def test_blocked_users_are_excluded_by_database(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "broadcast.db")
            await db.initialize()
            free = await db.upsert_user(1, "free", "Free")
            pro = await db.upsert_user(2, "pro", "Pro")
            premium = await db.upsert_user(3, "premium", "Premium")
            blocked = await db.upsert_user(4, "blocked", "Blocked")
            await db.set_admin_user_plan(pro.id, PRO)
            await db.set_admin_user_plan(premium.id, PREMIUM)
            await db.set_user_blocked(blocked.id, True)
            all_ids = {
                item.telegram_id
                for item in await db.get_broadcast_recipients("all")
            }
            paid_ids = {
                item.telegram_id
                for item in await db.get_broadcast_recipients("paid")
            }
            self.assertEqual(all_ids, {1, 2, 3})
            self.assertEqual(paid_ids, {2, 3})

    async def test_delivery_statistics_and_block_marking(self) -> None:
        recipients = [
            BroadcastRecipient(1, 11, FREE, "ru"),
            BroadcastRecipient(2, 22, FREE, "ru"),
            BroadcastRecipient(3, 33, PRO, "en"),
        ]
        bot = SimpleNamespace(copy_message=AsyncMock())
        bot.copy_message.side_effect = [
            SimpleNamespace(),
            RuntimeError("bot blocked by user"),
            RuntimeError("network failure"),
        ]
        db = SimpleNamespace(
            get_broadcast_recipients=AsyncMock(return_value=recipients),
            set_user_blocked_by_telegram_id=AsyncMock(),
        )
        result = await deliver_broadcast(bot, db, "all", 100, 55)
        self.assertEqual(result, BroadcastResult(1, 2, 1, 3))
        db.set_user_blocked_by_telegram_id.assert_awaited_once_with(
            22,
            True,
        )


class NewsTests(unittest.IsolatedAsyncioTestCase):
    async def test_news_are_saved_and_filtered_by_language(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "news.db")
            await db.initialize()
            await db.save_news("RU", "Русская новость", "ru")
            await db.save_news("EN", "English news", "en")
            ru = await db.get_news("ru")
            en = await db.get_news("en")
            self.assertEqual([item.title for item in ru], ["RU"])
            self.assertEqual([item.title for item in en], ["EN"])

    async def test_news_command_shows_buttons(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="en")
            ),
            get_news=AsyncMock(
                return_value=[
                    NewsItem(
                        1,
                        "Update",
                        "New feature",
                        "en",
                        "2026-06-21T00:00:00+00:00",
                    )
                ]
            ),
        )
        await news_command(message, db)
        self.assertEqual(message.answer.await_count, 2)
        keyboard = message.answer.await_args.kwargs["reply_markup"]
        callbacks = {
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        }
        self.assertEqual(
            callbacks,
            {"nav:menu", "nav:premium", "news:feedback"},
        )


class BotCommandsTests(unittest.IsolatedAsyncioTestCase):
    async def test_required_commands_are_registered(self) -> None:
        bot = SimpleNamespace(set_my_commands=AsyncMock())
        await set_commands(bot)
        commands = {
            item.command
            for item in bot.set_my_commands.await_args.args[0]
        }
        self.assertEqual(
            commands,
            {
                "start",
                "help",
                "premium",
                "history",
                "settings",
                "templates",
                "news",
                "invite",
                "paysupport",
                "admin",
                "broadcast",
            },
        )
