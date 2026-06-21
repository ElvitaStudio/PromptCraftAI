from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.database import Database
from app.plans import PREMIUM_PLUS
from app.services.claude_service import ClaudeService


class ClaudeChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_claude_context_is_isolated_from_gpt(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "claude.db")
            await db.initialize()
            user = await db.upsert_user(2, "claude", "Claude")
            await db.set_admin_user_plan(user.id, PREMIUM_PLUS)
            gpt = await db.create_assistant_chat(user.id, "gpt", "GPT chat")
            claude = await db.create_assistant_chat(
                user.id, "claude", "Claude architecture"
            )
            await db.add_assistant_message(
                gpt.id, user.id, "gpt", "user", "GPT secret context"
            )
            await db.add_assistant_message(
                claude.id,
                user.id,
                "claude",
                "user",
                "Claude private context",
            )
            claude_messages = await db.get_assistant_messages(
                claude.id, user.id, "claude"
            )
            wrong_context = await db.get_assistant_messages(
                gpt.id, user.id, "claude"
            )
            self.assertEqual(
                [item.content for item in claude_messages],
                ["Claude private context"],
            )
            self.assertEqual(wrong_context, [])

    async def test_claude_search_and_delete(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "claude-search.db")
            await db.initialize()
            user = await db.upsert_user(3, "claude", "Claude")
            chat = await db.create_assistant_chat(
                user.id, "claude", "Backend review"
            )
            await db.add_assistant_message(
                chat.id,
                user.id,
                "claude",
                "user",
                "Review FastAPI architecture",
            )
            found = await db.get_assistant_chats(
                user.id, "claude", "FastAPI"
            )
            self.assertEqual([item.id for item in found], [chat.id])
            self.assertTrue(
                await db.delete_assistant_chat(
                    chat.id, user.id, "claude"
                )
            )

    async def test_claude_stub_is_bilingual(self) -> None:
        service = ClaudeService()
        messages = [{"role": "user", "content": "Architecture"}]
        self.assertIn("Claude Assistant", await service.reply(messages, "en"))
        self.assertIn("заглушку", await service.reply(messages, "ru"))
