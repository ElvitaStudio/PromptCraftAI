from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.assistant_keyboards import (
    assistant_chat_keyboard,
    assistant_chats_keyboard,
    assistants_menu_keyboard,
)
from app.database import Database
from app.plans import PREMIUM_PLUS
from app.services.claude_service import ClaudeService
from app.services.errors import AssistantConfigurationError


class FakeClient:
    def __init__(self, payload) -> None:
        self.payload = payload
        self.calls = []

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        payload = self.payload

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return payload

        return Response()


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

    async def test_claude_calls_real_messages_api_with_context(self) -> None:
        client = FakeClient(
            {"content": [{"type": "text", "text": "Claude reply"}]}
        )
        service = ClaudeService("anthropic-key", client=client)
        result = await service.reply(
            [
                {"role": "user", "content": "Question"},
                {"role": "assistant", "content": "Earlier reply"},
                {"role": "user", "content": "Follow-up"},
            ],
            "en",
        )
        self.assertEqual(result, "Claude reply")
        url, kwargs = client.calls[0]
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(kwargs["headers"]["x-api-key"], "anthropic-key")
        self.assertEqual(len(kwargs["json"]["messages"]), 3)
        self.assertEqual(
            kwargs["json"]["model"],
            "claude-sonnet-4-6",
        )

    async def test_claude_requires_api_key(self) -> None:
        with self.assertRaises(AssistantConfigurationError):
            await ClaudeService().reply(
                [{"role": "user", "content": "Hello"}],
                "en",
            )

    def test_workspace_contains_only_gpt_and_claude(self) -> None:
        callbacks = {
            button.callback_data
            for row in assistants_menu_keyboard("ru").inline_keyboard
            for button in row
            if button.callback_data.startswith("assistant:")
        }
        self.assertEqual(
            callbacks,
            {"assistant:gpt:list", "assistant:claude:list"},
        )
        list_callbacks = {
            button.callback_data
            for row in assistant_chats_keyboard(
                "claude", [], "en"
            ).inline_keyboard
            for button in row
        }
        self.assertTrue(
            {
                "assistant:claude:new",
                "assistant:claude:list",
                "assistant:claude:search",
            }.issubset(list_callbacks)
        )
        open_callbacks = {
            button.callback_data
            for row in assistant_chat_keyboard(
                "claude", 9, "ru"
            ).inline_keyboard
            for button in row
        }
        self.assertIn("assistant:claude:delete:9", open_callbacks)
