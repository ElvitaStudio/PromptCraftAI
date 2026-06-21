from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import aiosqlite

from app.daily_prompts import prompt_of_the_day
from app.database import Database, User
from app.handlers.commands import daily_prompt_command
from app.handlers.prompts import (
    PromptFlow,
    choose_mode,
    choose_response_style,
    generate_prompt,
)
from app.keyboards import (
    mode_keyboard,
    programmer_modes_keyboard,
    response_style_keyboard,
    workflow_keyboard,
)
from app.plans import FREE, PREMIUM
from app.programmer_templates import PROGRAMMER_TEMPLATES
from app.prompt_engineering import build_generation_instructions


class FakeState:
    def __init__(self, data=None) -> None:
        self.state = None
        self.data = dict(data or {})
        self.cleared = False

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)

    async def get_data(self):
        return dict(self.data)

    async def clear(self) -> None:
        self.cleared = True


class SelectionTests(unittest.IsolatedAsyncioTestCase):
    def test_difficulty_and_style_keyboards(self) -> None:
        levels = {
            button.callback_data
            for row in mode_keyboard("code", "codex", "ru").inline_keyboard
            for button in row
        }
        self.assertTrue(
            {
                "mode:code:codex:simple",
                "mode:code:codex:advanced",
                "mode:code:codex:expert",
            }.issubset(levels)
        )
        styles = {
            button.callback_data
            for row in response_style_keyboard(
                "code", "codex", "en"
            ).inline_keyboard
            for button in row
        }
        self.assertEqual(
            styles,
            {
                "style:code:codex:short",
                "style:code:codex:detailed",
                "style:code:codex:professional",
                "style:code:codex:expert",
            },
        )

    async def test_expert_is_blocked_for_non_premium(self) -> None:
        callback = SimpleNamespace(
            data="mode:code:codex:expert",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="ru")
            )
        )
        with patch("app.handlers.prompts.Message", SimpleNamespace):
            await choose_mode(callback, db, FakeState())
        self.assertTrue(callback.answer.await_args.kwargs["show_alert"])
        self.assertIn("Premium", callback.answer.await_args.args[0])
        callback.message.answer.assert_not_awaited()

    async def test_premium_can_select_expert(self) -> None:
        callback = SimpleNamespace(
            data="mode:code:codex:expert",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, PREMIUM, language="en")
            ),
            update_user_preferences=AsyncMock(),
        )
        state = FakeState()
        with patch("app.handlers.prompts.Message", SimpleNamespace):
            await choose_mode(callback, db, state)
        self.assertEqual(state.data["difficulty"], "expert")
        keyboard = callback.message.answer.await_args.kwargs["reply_markup"]
        callbacks = {
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        }
        self.assertIn("style:code:codex:professional", callbacks)

    async def test_response_style_is_saved_to_state_and_database(self) -> None:
        callback = SimpleNamespace(
            data="style:code:cursor:detailed",
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
        state = FakeState({"workflow": "create"})
        with patch("app.handlers.prompts.Message", SimpleNamespace):
            await choose_response_style(callback, db, state)
        self.assertEqual(state.state, PromptFlow.waiting_for_task)
        self.assertEqual(state.data["response_style"], "detailed")
        db.update_user_preferences.assert_awaited_once_with(
            1,
            category="code",
            target_ai="cursor",
            response_style="detailed",
        )


class PreferenceDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_preferences_are_persisted(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "preferences.db")
            await db.initialize()
            await db.upsert_user(42, "dev", "Dev")
            await db.update_user_preferences(
                42,
                category="code",
                target_ai="claude_code",
                difficulty="advanced",
                response_style="detailed",
                workflow="optimize",
            )
            user = await db.get_user_by_telegram_id(42)
            self.assertEqual(user.last_category, "code")
            self.assertEqual(user.last_target_ai, "claude_code")
            self.assertEqual(user.last_difficulty, "advanced")
            self.assertEqual(user.last_response_style, "detailed")
            self.assertEqual(user.last_workflow, "optimize")

    async def test_legacy_users_table_gets_preference_columns(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "legacy-preferences.db"
            async with aiosqlite.connect(path) as db:
                await db.execute(
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
                await db.commit()
            database = Database(path)
            await database.initialize()
            async with database._connect() as db:
                columns = {
                    row[1]
                    for row in await (
                        await db.execute("PRAGMA table_info(users)")
                    ).fetchall()
                }
            self.assertTrue(
                {
                    "last_category",
                    "last_target_ai",
                    "last_difficulty",
                    "last_response_style",
                    "last_workflow",
                    "export_format",
                }.issubset(columns)
            )


class DailyPromptTests(unittest.IsolatedAsyncioTestCase):
    def test_prompt_of_the_day_is_deterministic_and_localized(self) -> None:
        selected_date = date(2026, 6, 21)
        ru = prompt_of_the_day("ru", selected_date)
        en = prompt_of_the_day("en", selected_date)
        self.assertEqual(ru, prompt_of_the_day("ru", selected_date))
        self.assertIn("Ты —", ru)
        self.assertIn("You are", en)

    async def test_daily_command_saves_and_shows_prompt(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(7, 1, FREE, language="en")
            ),
            save_prompt=AsyncMock(return_value=99),
        )
        await daily_prompt_command(message, db)
        db.save_prompt.assert_awaited_once()
        keyboard = message.answer.await_args.kwargs["reply_markup"]
        callbacks = {
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        }
        self.assertIn("prompt:copy:99", callbacks)


class OptimizePromptTests(unittest.IsolatedAsyncioTestCase):
    async def test_optimize_workflow_uses_optimizer(self) -> None:
        status = SimpleNamespace(edit_text=AsyncMock())
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            text="make this code better",
            answer=AsyncMock(return_value=status),
        )
        user = User(7, 1, FREE, language="en")
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(return_value=user),
            reserve_request=AsyncMock(return_value=True),
            save_prompt=AsyncMock(return_value=12),
            release_request=AsyncMock(),
        )
        service = SimpleNamespace(
            optimize_prompt=AsyncMock(return_value="Professional prompt"),
        )
        state = FakeState(
            {
                "category": "code",
                "target_ai": "cursor",
                "difficulty": "advanced",
                "response_style": "professional",
                "workflow": "optimize",
                "variants": 1,
            }
        )
        await generate_prompt(message, db, service, state)
        service.optimize_prompt.assert_awaited_once()
        self.assertEqual(
            db.save_prompt.await_args.args[5],
            "optimize:advanced:professional",
        )
        self.assertTrue(state.cleared)


class ProfessionalGenerationTests(unittest.TestCase):
    def test_coding_assistants_receive_full_engineering_structure(self) -> None:
        required = (
            "Role of the specialist",
            "Goal",
            "Stack and versions",
            "Project structure",
            "Constraints",
            "Required response format",
            "Tests",
            "Error handling",
            "Documentation",
        )
        for target in ("claude_code", "codex", "cursor"):
            with self.subTest(target=target):
                instructions = build_generation_instructions(
                    "code",
                    target,
                    "en",
                    "expert",
                    "professional",
                    1,
                    "create",
                )
                for section in required:
                    self.assertIn(section, instructions)
                self.assertIn(target.replace("_", " ").split()[0].title(), instructions)

    def test_programmer_modes_and_workflow_buttons_are_localized(self) -> None:
        self.assertEqual(len(PROGRAMMER_TEMPLATES), 13)
        callbacks = {
            button.callback_data
            for row in programmer_modes_keyboard("ru").inline_keyboard
            for button in row
        }
        self.assertIn("devmode:telegram_mini_app", callbacks)
        ru = [
            button.text
            for row in workflow_keyboard("ru", True).inline_keyboard
            for button in row
        ]
        en = [
            button.text
            for row in workflow_keyboard("en", True).inline_keyboard
            for button in row
        ]
        self.assertIn("✍ Создать промпт", ru)
        self.assertIn("🔧 Улучшить промпт", ru)
        self.assertIn("🔥 Промпт дня", ru)
        self.assertIn("✍ Create Prompt", en)
        self.assertIn("🔧 Optimize Prompt", en)
        self.assertIn("🔥 Prompt of the Day", en)
