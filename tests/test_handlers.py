from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from app.database import RegistrationResult, User
from app.handlers.commands import premium_command, start_command
from app.handlers.language import select_language
from app.handlers.prompts import PromptFlow, choose_ai
from app.keyboards import language_keyboard, premium_keyboard
from app.plans import FREE, PREMIUM


class FakeState:
    def __init__(self) -> None:
        self.state = None
        self.data = {}

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_start_requests_language(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(
                id=1,
                username="user",
                first_name="User",
                last_name=None,
            ),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            register_user=AsyncMock(
                return_value=RegistrationResult(
                    User(1, 1, FREE),
                    True,
                    False,
                )
            )
        )
        command = SimpleNamespace(args=None)

        await start_command(message, command, db)

        _, kwargs = message.answer.await_args
        self.assertEqual(kwargs["reply_markup"], language_keyboard())

    async def test_language_callback_persists_choice(self) -> None:
        callback = SimpleNamespace(
            data="language:en",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(set_language=AsyncMock())

        with unittest.mock.patch(
            "app.handlers.language.Message",
            SimpleNamespace,
        ):
            await select_language(callback, db)

        db.set_language.assert_awaited_once_with(1, "en")
        self.assertIn(
            "Language saved",
            callback.message.answer.await_args.args[0],
        )

    async def test_free_user_goes_directly_to_task(self) -> None:
        callback = SimpleNamespace(
            data="ai:text:chatgpt",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="en")
            )
        )
        state = FakeState()

        with unittest.mock.patch(
            "app.handlers.prompts.Message",
            SimpleNamespace,
        ):
            await choose_ai(callback, db, state)

        self.assertEqual(state.state, PromptFlow.waiting_for_task)
        self.assertEqual(state.data["target_ai"], "chatgpt")

    async def test_premium_user_sees_modes(self) -> None:
        callback = SimpleNamespace(
            data="ai:code:codex",
            from_user=SimpleNamespace(id=1),
            message=SimpleNamespace(answer=AsyncMock()),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, PREMIUM, language="ru")
            )
        )

        with unittest.mock.patch(
            "app.handlers.prompts.Message",
            SimpleNamespace,
        ):
            await choose_ai(callback, db, FakeState())

        keyboard = callback.message.answer.await_args.kwargs["reply_markup"]
        callbacks = {
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        }
        self.assertIn("mode:code:codex:expert", callbacks)
        self.assertIn("mode:code:codex:variants", callbacks)

    async def test_premium_command_uses_stars_keyboard(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=1),
            answer=AsyncMock(),
        )
        db = SimpleNamespace(
            get_user_by_telegram_id=AsyncMock(
                return_value=User(1, 1, FREE, language="en")
            )
        )
        await premium_command(message, db)
        self.assertEqual(
            message.answer.await_args.kwargs["reply_markup"],
            premium_keyboard(),
        )
