from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.assistant_keyboards import assistants_menu_keyboard
from app.database import Database
from app.plans import PREMIUM_PLUS
from app.services.gemini_service import GeminiService


class GeminiChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_gemini_chats_are_user_isolated(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "gemini.db")
            await db.initialize()
            first = await db.upsert_user(10, "first", "First")
            second = await db.upsert_user(20, "second", "Second")
            await db.set_admin_user_plan(first.id, PREMIUM_PLUS)
            await db.set_admin_user_plan(second.id, PREMIUM_PLUS)
            chat = await db.create_assistant_chat(
                first.id, "gemini", "Research"
            )
            await db.add_assistant_message(
                chat.id,
                first.id,
                "gemini",
                "user",
                "Private research",
            )
            self.assertIsNone(
                await db.get_assistant_chat(chat.id, second.id, "gemini")
            )
            self.assertEqual(
                await db.get_assistant_messages(
                    chat.id, second.id, "gemini"
                ),
                [],
            )
            self.assertFalse(
                await db.delete_assistant_chat(
                    chat.id, second.id, "gemini"
                )
            )

    async def test_gemini_history_and_search(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "gemini-history.db")
            await db.initialize()
            user = await db.upsert_user(30, "gemini", "Gemini")
            chat = await db.create_assistant_chat(
                user.id, "gemini", "Market research"
            )
            await db.add_assistant_message(
                chat.id,
                user.id,
                "gemini",
                "user",
                "Analyze the robotics market",
            )
            chats = await db.get_assistant_chats(
                user.id, "gemini", "robotics"
            )
            self.assertEqual(chats[0].assistant, "gemini")
            self.assertEqual(
                (
                    await db.get_assistant_messages(
                        chat.id, user.id, "gemini"
                    )
                )[0].content,
                "Analyze the robotics market",
            )

    async def test_gemini_stub_and_menu_localization(self) -> None:
        service = GeminiService()
        messages = [{"role": "user", "content": "Research"}]
        self.assertIn("safe stub", await service.reply(messages, "en"))
        self.assertIn("заглушку", await service.reply(messages, "ru"))
        callbacks = {
            button.callback_data
            for row in assistants_menu_keyboard("ru").inline_keyboard
            for button in row
        }
        self.assertTrue(
            {
                "assistant:gpt:list",
                "assistant:claude:list",
                "assistant:gemini:list",
            }.issubset(callbacks)
        )
