from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from app.database import Database, PromptRecord, User
from app.handlers.history import (
    export_history_prompt,
    favorite_history_prompt,
    history_card,
    open_history_prompt,
    reuse_history_prompt,
    show_history_page,
)
from app.handlers.prompt_chat import (
    PromptChatFlow,
    chat_idea,
    finish_prompt_chat,
    prompt_chat_start,
)
from app.handlers.settings import save_preference, settings_text
from app.keyboards import (
    history_list_keyboard,
    premium_keyboard,
    prompt_chat_ai_keyboard,
    settings_ai_keyboard,
    settings_keyboard,
    workflow_keyboard,
)
from app.plans import FREE, PREMIUM, PRO, get_plan_limits
from app.services.openai_service import OpenAIService
from app.subscriptions import premium_text


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


def record(prompt_id: int = 7, language: str = "ru") -> PromptRecord:
    return PromptRecord(
        prompt_id,
        1,
        "code",
        "codex",
        "Создай Telegram-бота",
        "Ты — senior Python developer...",
        "create:advanced:professional",
        "2026-06-21T10:00:00+00:00",
        language,
    )


class MainMenuTests(unittest.TestCase):
    def test_main_menu_contains_all_ru_en_actions(self) -> None:
        ru = {
            button.text
            for row in workflow_keyboard("ru", True).inline_keyboard
            for button in row
        }
        en = {
            button.text
            for row in workflow_keyboard("en", True).inline_keyboard
            for button in row
        }
        self.assertTrue(
            {
                "✍ Создать промпт",
                "🔧 Улучшить промпт",
                "📜 История",
                "⭐ Избранное",
                "📚 Шаблоны",
                "🔥 Промпт дня",
                "👑 Premium",
                "⚙️ Настройки",
                "💬 Prompt Chat",
            }.issubset(ru)
        )
        self.assertIn("✍ Create Prompt", en)
        self.assertIn("🔧 Optimize Prompt", en)
        self.assertIn("📜 History", en)
        self.assertIn("⚙️ Settings", en)


class HistoryPaginationTests(unittest.IsolatedAsyncioTestCase):
    async def test_history_page_is_limited_and_paginated(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "history.db")
            await db.initialize()
            user = await db.upsert_user(1, "history", "History")
            await db.set_admin_user_plan(user.id, PREMIUM)
            user = await db.get_user_by_telegram_id(1)
            for index in range(12):
                await db.save_prompt(
                    user.id,
                    "text",
                    "chatgpt",
                    f"source {index}",
                    f"prompt {index}",
                    "standard",
                    "en",
                )
            first = await db.get_prompt_history_page(user, 0)
            third = await db.get_prompt_history_page(user, 2)
            self.assertEqual(len(first.prompts), 5)
            self.assertEqual(len(third.prompts), 2)
            self.assertEqual((third.page, third.total_pages), (2, 3))

    async def test_history_list_and_card_include_metadata(self) -> None:
        message = SimpleNamespace(answer=AsyncMock())
        page = SimpleNamespace(
            prompts=[record()],
            page=0,
            total_pages=1,
            total_prompts=1,
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="ru")
            ),
            get_prompt_history_page=AsyncMock(return_value=page),
        )
        await show_history_page(message, db, 1)
        keyboard = message.answer.await_args.kwargs["reply_markup"]
        callbacks = {
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        }
        self.assertIn("history:open:7:0", callbacks)
        card = history_card(record(), "ru")
        self.assertIn("Исходный запрос", card)
        self.assertIn("Итоговый промпт", card)
        self.assertIn("Codex", card)
        self.assertIn("21.06.2026", card)

    async def test_history_open_reuse_favorite_and_export(self) -> None:
        user = User(
            1, 1, FREE, language="en", export_format="markdown"
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(return_value=user),
            get_prompt=AsyncMock(return_value=record(language="en")),
            add_favorite=AsyncMock(return_value=True),
        )
        message = SimpleNamespace(
            answer=AsyncMock(),
            answer_document=AsyncMock(),
        )
        with patch("app.handlers.history.Message", SimpleNamespace):
            open_callback = SimpleNamespace(
                data="history:open:7:0",
                from_user=SimpleNamespace(id=1),
                message=message,
                answer=AsyncMock(),
            )
            await open_history_prompt(open_callback, db)
            keyboard = message.answer.await_args.kwargs["reply_markup"]
            callbacks = {
                button.callback_data
                for row in keyboard.inline_keyboard
                for button in row
            }
            self.assertIn("history:reuse:7", callbacks)
            self.assertIn("history:favorite:7", callbacks)
            self.assertIn("history:export:7", callbacks)

            reuse = SimpleNamespace(
                data="history:reuse:7",
                from_user=SimpleNamespace(id=1),
                message=message,
                answer=AsyncMock(),
            )
            await reuse_history_prompt(reuse, db)
            self.assertIn("senior Python", message.answer.await_args.args[0])

            favorite = SimpleNamespace(
                data="history:favorite:7",
                from_user=SimpleNamespace(id=1),
                message=message,
                answer=AsyncMock(),
            )
            await favorite_history_prompt(favorite, db)
            db.add_favorite.assert_awaited_once()

            export = SimpleNamespace(
                data="history:export:7",
                from_user=SimpleNamespace(id=1),
                message=message,
                answer=AsyncMock(),
            )
            await export_history_prompt(export, db)
            document = message.answer_document.await_args.args[0]
            self.assertTrue(document.filename.endswith(".md"))

    def test_history_keyboard_has_navigation(self) -> None:
        keyboard = history_list_keyboard(
            [(1, "One"), (2, "Two")],
            1,
            3,
            "en",
        )
        callbacks = {
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        }
        self.assertIn("history:page:0", callbacks)
        self.assertIn("history:page:2", callbacks)


class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def test_settings_are_persisted_and_used(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "settings.db")
            await db.initialize()
            await db.upsert_user(1, "settings", "Settings")
            await db.update_user_preferences(
                1,
                target_ai="cursor",
                difficulty="advanced",
                response_style="creative",
                export_format="markdown",
            )
            user = await db.get_user_by_telegram_id(1)
            self.assertEqual(user.last_target_ai, "cursor")
            self.assertEqual(user.last_difficulty, "advanced")
            self.assertEqual(user.last_response_style, "creative")
            self.assertEqual(user.export_format, "markdown")
            self.assertIn("Creative", settings_text(user))
            self.assertIn("Markdown", settings_text(user))

    async def test_expert_setting_is_premium_only(self) -> None:
        callback = SimpleNamespace(
            data="pref:difficulty:expert",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="en")
            ),
            update_user_preferences=AsyncMock(),
        )
        await save_preference(callback, db)
        db.update_user_preferences.assert_not_awaited()
        self.assertIn("Premium", callback.answer.await_args.args[0])

    def test_settings_keyboards_cover_all_options(self) -> None:
        sections = {
            button.callback_data
            for row in settings_keyboard("ru").inline_keyboard
            for button in row
        }
        self.assertTrue(
            {
                "settings:language",
                "settings:style",
                "settings:difficulty",
                "settings:ai",
                "settings:export",
            }.issubset(sections)
        )
        ai_callbacks = {
            button.callback_data
            for row in settings_ai_keyboard("en").inline_keyboard
            for button in row
        }
        self.assertEqual(
            len([item for item in ai_callbacks if item.startswith("pref:ai:")]),
            13,
        )


class PremiumSectionTests(unittest.TestCase):
    def test_plans_are_localized_and_have_payment_buttons(self) -> None:
        ru = premium_text("ru")
        en = premium_text("en")
        self.assertIn("2 варианта", ru)
        self.assertIn("Expert Mode", ru)
        self.assertIn("2 prompt variants", en)
        self.assertIn("Markdown export", en)
        buttons = {
            button.callback_data
            for row in premium_keyboard("ru").inline_keyboard
            for button in row
        }
        self.assertIn("payment:pro", buttons)
        self.assertIn("payment:premium", buttons)
        self.assertEqual(get_plan_limits(PRO).response_variants, 2)


class PromptChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_prompt_chat_starts_and_asks_localized_questions(self) -> None:
        message = SimpleNamespace(answer=AsyncMock())
        callback = SimpleNamespace(
            data="promptchat:start",
            from_user=SimpleNamespace(id=1),
            message=message,
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="ru")
            )
        )
        state = FakeState()
        with patch("app.handlers.prompt_chat.Message", SimpleNamespace):
            await prompt_chat_start(callback, db, state)
        self.assertEqual(state.state, PromptChatFlow.idea)
        self.assertIn("Опишите вашу идею", message.answer.await_args.args[0])

        idea_message = SimpleNamespace(
            text="Telegram Mini App для шахмат",
            answer=AsyncMock(),
        )
        await chat_idea(idea_message, state)
        self.assertEqual(state.state, PromptChatFlow.project_language)
        self.assertIn("На каком языке", idea_message.answer.await_args.args[0])

    async def test_prompt_chat_finishes_with_pro_variants(self) -> None:
        data = {
            "chat_language": "en",
            "idea": "Chess Telegram Mini App",
            "project_language": "English",
            "audience": "Chess players",
            "features": "Matches and rating",
            "design": "Minimal",
            "monetization": "Stars",
            "technologies": "React and FastAPI",
        }
        status = SimpleNamespace(edit_text=AsyncMock())
        message = SimpleNamespace(
            answer=AsyncMock(return_value=status),
        )
        callback = SimpleNamespace(
            data="promptchat:ai:deepseek",
            from_user=SimpleNamespace(id=1),
            message=message,
            answer=AsyncMock(),
        )
        user = User(
            7, 1, PRO, language="en",
            last_difficulty="advanced",
            last_response_style="professional",
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(return_value=user),
            reserve_request=AsyncMock(return_value=True),
            save_prompt=AsyncMock(return_value=55),
            release_request=AsyncMock(),
        )
        service = SimpleNamespace(
            generate_prompt_chat=AsyncMock(
                return_value="Professional DeepSeek prompt"
            )
        )
        with patch("app.handlers.prompt_chat.Message", SimpleNamespace):
            await finish_prompt_chat(
                callback,
                db,
                service,
                FakeState(data),
            )
        self.assertEqual(
            service.generate_prompt_chat.await_args.kwargs["variants"],
            2,
        )
        self.assertEqual(db.save_prompt.await_args.args[2], "deepseek")

    def test_prompt_chat_ai_keyboard_has_six_models(self) -> None:
        callbacks = {
            button.callback_data
            for row in prompt_chat_ai_keyboard("ru").inline_keyboard
            for button in row
        }
        self.assertEqual(
            callbacks,
            {
                "promptchat:ai:claude_code",
                "promptchat:ai:codex",
                "promptchat:ai:cursor",
                "promptchat:ai:chatgpt",
                "promptchat:ai:gemini",
                "promptchat:ai:deepseek",
            },
        )


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text="Ready chat prompt")


class PromptChatServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_builds_professional_deepseek_prompt(self) -> None:
        service = object.__new__(OpenAIService)
        service.client = SimpleNamespace(responses=FakeResponses())
        service.generation_model = "test-model"
        result = await service.generate_prompt_chat(
            {
                "idea": "App",
                "audience": "Users",
                "features": "Core features",
            },
            "deepseek",
            "en",
            variants=2,
        )
        self.assertEqual(result, "Ready chat prompt")
        instructions = service.client.responses.kwargs["instructions"]
        self.assertIn("DeepSeek", instructions)
        self.assertIn("testing strategy", instructions)
        self.assertIn("Variants: 2", instructions)
