from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import aiosqlite

from app.database import AdminUser, Database, PromptRecord, User
from app.exports import prompt_markdown, prompt_txt
from app.handlers.admin import AdminFlow, admin_callback, admin_search
from app.handlers.commands import favorites_command, templates_command
from app.handlers.prompts import (
    PromptFlow,
    choose_template,
    handle_prompt_action,
)
from app.keyboards import (
    prompt_actions_keyboard,
    template_items_keyboard,
    templates_keyboard,
)
from app.templates import TEMPLATE_GROUPS, TEMPLATES, templates_for_group


class FakeState:
    def __init__(self) -> None:
        self.state = None
        self.data = {}
        self.cleared = False

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)

    async def clear(self) -> None:
        self.cleared = True


def prompt_record(language: str = "ru") -> PromptRecord:
    return PromptRecord(
        id=7,
        user_id=1,
        category="code",
        target_ai="codex",
        source_text="Создай API",
        prompt_text="Готовый промпт",
        mode="standard",
        created_at="2026-06-20T10:00:00+00:00",
        language=language,
    )


class PromptActionKeyboardTests(unittest.TestCase):
    def test_all_post_generation_buttons_ru(self) -> None:
        buttons = [
            (button.text, button.callback_data)
            for row in prompt_actions_keyboard(7, "ru").inline_keyboard
            for button in row
        ]
        self.assertEqual(
            buttons,
            [
                ("📋 Копировать", "prompt:copy:7"),
                ("✨ Улучшить", "prompt:improve:7"),
                ("📏 Короче", "prompt:shorter:7"),
                ("📝 Подробнее", "prompt:details:7"),
                (
                    "🇬🇧 Перевести на английский",
                    "prompt:translate_en:7",
                ),
                ("🔄 Другой вариант", "prompt:variant:7"),
                ("⭐ В избранное", "prompt:favorite:7"),
                ("📄 Export TXT", "prompt:export_txt:7"),
                ("📝 Export MD", "prompt:export_md:7"),
            ],
        )

    def test_all_post_generation_buttons_en(self) -> None:
        texts = {
            button.text
            for row in prompt_actions_keyboard(7, "en").inline_keyboard
            for button in row
        }
        self.assertIn("📋 Copy", texts)
        self.assertIn("✨ Improve", texts)
        self.assertIn("🔄 Another variant", texts)
        self.assertIn("⭐ Favorite", texts)


class TemplateTests(unittest.IsolatedAsyncioTestCase):
    def test_template_library_has_required_groups_and_items(self) -> None:
        self.assertEqual(
            set(TEMPLATE_GROUPS),
            {"business", "code", "images", "video"},
        )
        self.assertEqual(len(TEMPLATES), 12)
        self.assertEqual(
            [item.title("en") for item in templates_for_group("code")],
            ["Python", "React", "SQL"],
        )
        self.assertEqual(
            [item.title("ru") for item in templates_for_group("video")],
            ["Kling", "Veo", "Runway"],
        )

    def test_template_keyboards_are_localized(self) -> None:
        ru = [
            button.text
            for row in templates_keyboard("ru").inline_keyboard
            for button in row
        ]
        en = [
            button.text
            for row in templates_keyboard("en").inline_keyboard
            for button in row
        ]
        self.assertIn("💼 Бизнес", ru)
        self.assertIn("💼 Business", en)
        callbacks = {
            button.callback_data
            for row in template_items_keyboard("images", "en").inline_keyboard
            for button in row
        }
        self.assertIn("template:image_midjourney", callbacks)

    async def test_template_prepares_prompt_structure(self) -> None:
        callback = SimpleNamespace(
            data="template:code_python",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, "free", language="en")
            )
        )
        state = FakeState()
        with patch("app.handlers.prompts.Message", SimpleNamespace):
            await choose_template(callback, db, state)
        self.assertEqual(state.state, PromptFlow.waiting_for_task)
        self.assertEqual(state.data["target_ai"], "codex")
        self.assertIn("acceptance criteria", state.data["template_structure"])


class ExportTests(unittest.IsolatedAsyncioTestCase):
    def test_txt_export_is_clean_prompt(self) -> None:
        self.assertEqual(prompt_txt(prompt_record()), "Готовый промпт".encode())

    def test_markdown_export_contains_metadata(self) -> None:
        text = prompt_markdown(prompt_record("en")).decode()
        self.assertIn("# PromptCraft AI", text)
        self.assertIn("**AI:** Codex", text)
        self.assertIn("## Prompt", text)

    async def test_export_handlers_send_files(self) -> None:
        for action, extension in (("export_txt", ".txt"), ("export_md", ".md")):
            with self.subTest(action=action):
                message = SimpleNamespace(
                    answer_document=AsyncMock(),
                    answer=AsyncMock(),
                )
                callback = SimpleNamespace(
                    data=f"prompt:{action}:7",
                    from_user=SimpleNamespace(id=1),
                    message=message,
                    answer=AsyncMock(),
                )
                db = SimpleNamespace(
                    get_user_by_telegram_id=AsyncMock(
                        return_value=User(1, 1, "free", language="ru")
                    ),
                    get_prompt=AsyncMock(return_value=prompt_record()),
                )
                with patch("app.handlers.prompts.Message", SimpleNamespace):
                    await handle_prompt_action(
                        callback,
                        db,
                        SimpleNamespace(),
                    )
                document = message.answer_document.await_args.args[0]
                self.assertTrue(document.filename.endswith(extension))


class FavoriteTests(unittest.IsolatedAsyncioTestCase):
    async def test_favorite_is_saved_once_and_can_be_opened(self) -> None:
        with TemporaryDirectory() as temp:
            db = Database(Path(temp) / "favorites.db")
            await db.initialize()
            user = await db.upsert_user(1, "favorite_user", "Favorite")
            prompt_id = await db.save_prompt(
                user.id,
                "text",
                "chatgpt",
                "source",
                "favorite prompt",
                "standard",
                "en",
            )
            self.assertTrue(
                await db.add_favorite(user.id, prompt_id, "My prompt")
            )
            self.assertFalse(
                await db.add_favorite(user.id, prompt_id, "Duplicate")
            )
            favorites = await db.get_favorites(user.id)
            self.assertEqual(len(favorites), 1)
            opened = await db.get_favorite(favorites[0].id, user.id)
            self.assertEqual(opened.prompt.prompt_text, "favorite prompt")
            self.assertEqual(opened.prompt.language, "en")

    async def test_favorites_command_is_localized(self) -> None:
        for language, expected in (("ru", "Избранное"), ("en", "Favorites")):
            message = SimpleNamespace(
                from_user=SimpleNamespace(id=1),
                answer=AsyncMock(),
            )
            db = SimpleNamespace(
                get_user_by_telegram_id=AsyncMock(
                    return_value=User(1, 1, "free", language=language)
                ),
                get_favorites=AsyncMock(return_value=[]),
            )
            await favorites_command(message, db)
            self.assertIn(expected, message.answer.await_args.args[0])


class AdminHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_block_callback(self) -> None:
        user = AdminUser(
            5, 55, "target", "Target", None, "Target", "ru",
            "free", None, None, True, "2026-01-01",
        )
        message = SimpleNamespace(edit_text=AsyncMock())
        callback = SimpleNamespace(
            data="admin:block:5:0:-",
            from_user=SimpleNamespace(id=99),
            message=message,
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            set_user_blocked=AsyncMock(return_value=True),
            get_admin_user=AsyncMock(return_value=user),
        )
        settings = SimpleNamespace(admin_ids=frozenset({99}))
        with patch("app.handlers.admin.Message", SimpleNamespace):
            await admin_callback(
                callback,
                db,
                settings,
                FakeState(),
            )
        db.set_user_blocked.assert_awaited_once_with(5, True)

    async def test_admin_search_passes_id_or_username(self) -> None:
        page = SimpleNamespace(
            users=[],
            page=0,
            total_users=0,
            total_pages=1,
        )
        for query in ("123456", "@username"):
            with self.subTest(query=query):
                message = SimpleNamespace(
                    from_user=SimpleNamespace(id=99),
                    text=query,
                    answer=AsyncMock(),
                )
                db = SimpleNamespace(
                    get_admin_users_page=AsyncMock(return_value=page)
                )
                await admin_search(
                    message,
                    db,
                    SimpleNamespace(admin_ids=frozenset({99})),
                    FakeState(),
                )
                db.get_admin_users_page.assert_awaited_once_with(
                    0,
                    search=query,
                )


class LocalizationTests(unittest.IsolatedAsyncioTestCase):
    async def test_templates_command_ru_en(self) -> None:
        for language, expected in (("ru", "Шаблоны"), ("en", "Templates")):
            message = SimpleNamespace(
                from_user=SimpleNamespace(id=1),
                answer=AsyncMock(),
            )
            db = SimpleNamespace(
                get_user_by_telegram_id=AsyncMock(
                    return_value=User(1, 1, "free", language=language)
                )
            )
            await templates_command(message, db)
            self.assertIn(expected, message.answer.await_args.args[0])


class MigrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_old_prompts_table_gets_language_and_favorites(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.db"
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
                await db.execute(
                    """
                    CREATE TABLE prompts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        target_ai TEXT NOT NULL,
                        source_text TEXT NOT NULL,
                        prompt_text TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        created_at TEXT NOT NULL
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
                        await db.execute("PRAGMA table_info(prompts)")
                    ).fetchall()
                }
                tables = {
                    row[0]
                    for row in await (
                        await db.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )
                    ).fetchall()
                }
            self.assertIn("language", columns)
            self.assertIn("favorites", tables)
