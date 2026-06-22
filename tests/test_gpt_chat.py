from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import aiosqlite

from app.database import Database, User
from app.handlers.assistants import assistants_menu
from app.handlers.gpt_chat import GPTChatFlow, gpt_user_message
from app.plans import FREE, PREMIUM_PLUS
from app.services.gpt_service import GPTService


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


class GPTChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_chat_save_messages_search_and_delete(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "gpt.db")
            await db.initialize()
            user = await db.upsert_user(1, "plus", "Plus")
            await db.set_admin_user_plan(user.id, PREMIUM_PLUS)
            chat = await db.create_assistant_chat(
                user.id, "gpt", "Product strategy"
            )
            await db.add_assistant_message(
                chat.id, user.id, "gpt", "user", "Build a roadmap"
            )
            await db.add_assistant_message(
                chat.id, user.id, "gpt", "assistant", "Roadmap response"
            )
            messages = await db.get_assistant_messages(
                chat.id, user.id, "gpt"
            )
            self.assertEqual(
                [(item.role, item.content) for item in messages],
                [
                    ("user", "Build a roadmap"),
                    ("assistant", "Roadmap response"),
                ],
            )
            by_title = await db.get_assistant_chats(
                user.id, "gpt", "strategy"
            )
            by_message = await db.get_assistant_chats(
                user.id, "gpt", "roadmap response"
            )
            self.assertEqual(by_title[0].id, chat.id)
            self.assertEqual(by_message[0].id, chat.id)
            self.assertTrue(
                await db.delete_assistant_chat(chat.id, user.id, "gpt")
            )
            self.assertEqual(
                await db.get_assistant_messages(chat.id, user.id, "gpt"),
                [],
            )

    async def test_gpt_handler_preserves_context(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            text="Second question",
            answer=AsyncMock(),
        )
        user = User(7, 1, PREMIUM_PLUS, language="en")
        existing = [
            SimpleNamespace(role="user", content="First question"),
            SimpleNamespace(role="assistant", content="First answer"),
        ]
        updated = [
            *existing,
            SimpleNamespace(role="user", content="Second question"),
        ]
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(return_value=user),
            get_assistant_messages=AsyncMock(
                side_effect=[existing, updated]
            ),
            add_assistant_message=AsyncMock(),
            rename_assistant_chat=AsyncMock(),
        )
        service = SimpleNamespace(reply=AsyncMock(return_value="Second answer"))
        await gpt_user_message(
            message,
            db,
            FakeState(
                {
                    "assistant_chat_id": 10,
                    "active_assistant": "gpt",
                }
            ),
            service,
        )
        context = service.reply.await_args.args[0]
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0]["content"], "First question")
        db.add_assistant_message.assert_any_await(
            10, 7, "gpt", "assistant", "Second answer"
        )

    async def test_non_plus_user_sees_upgrade(self) -> None:
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="ru")
            )
        )
        with patch("app.handlers.assistants.Message", SimpleNamespace):
            await assistants_menu(callback, db)
        self.assertIn(
            "Premium Plus",
            callback.message.answer.await_args.args[0],
        )

    async def test_gpt_stub_is_bilingual(self) -> None:
        service = GPTService()
        messages = [{"role": "user", "content": "Hello"}]
        self.assertIn("stub", await service.reply(messages, "en"))
        self.assertIn("заглушка", await service.reply(messages, "ru"))

    async def test_legacy_database_gets_assistant_tables(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.db"
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
                        is_blocked INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                    )
                    """
                )
                await connection.commit()
            db = Database(path)
            await db.initialize()
            async with db._connect() as connection:
                tables = {
                    row[0]
                    for row in await (
                        await connection.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )
                    ).fetchall()
                }
            self.assertIn("assistant_chats", tables)
            self.assertIn("assistant_messages", tables)

    async def test_legacy_gemini_rows_remain_compatible(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "legacy-gemini.db")
            await db.initialize()
            user = await db.upsert_user(4, "legacy", "Legacy")
            chat = await db.create_assistant_chat(
                user.id, "gemini", "Legacy Gemini chat"
            )
            await db.add_assistant_message(
                chat.id,
                user.id,
                "gemini",
                "user",
                "Preserved legacy message",
            )
            messages = await db.get_assistant_messages(
                chat.id, user.id, "gemini"
            )
            self.assertEqual(
                [item.content for item in messages],
                ["Preserved legacy message"],
            )
