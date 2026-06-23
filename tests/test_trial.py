from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.database import Database, User
from app.middlewares import TrialCallbackMiddleware, UserProfileMiddleware
from app.database import RegistrationResult
from app.handlers.commands import start_command
from app.plans import (
    FREE,
    PREMIUM_PLUS,
    TRIAL_AI_REQUEST_LIMIT,
    has_assistant_access,
    has_premium_features,
)
from app.trial import (
    existing_user_trial_message,
    new_user_trial_message,
    trial_status_text,
)


class TrialDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "trial.db")
        await self.db.initialize()
        self.user = await self.db.upsert_user(
            100,
            "trial_user",
            "Trial",
        )

    async def asyncTearDown(self) -> None:
        self.temp.cleanup()

    async def test_trial_is_granted_once_for_24_hours(self) -> None:
        before = datetime.now(timezone.utc)
        first = await self.db.activate_trial_once(100)
        second = await self.db.activate_trial_once(100)
        self.assertTrue(first.activated_now)
        self.assertTrue(first.notification_required)
        self.assertFalse(second.activated_now)
        self.assertFalse(second.notification_required)
        expires = datetime.fromisoformat(first.user.trial_expires_at)
        self.assertGreaterEqual(
            expires,
            before + timedelta(hours=23, minutes=59),
        )
        self.assertTrue(first.user.trial_active)
        self.assertEqual(
            first.user.entitlement_plan,
            PREMIUM_PLUS,
        )

    async def test_trial_has_one_atomic_shared_counter(self) -> None:
        activation = await self.db.activate_trial_once(100)
        results = await asyncio.gather(
            *[
                self.db.reserve_ai_request(activation.user)
                for _ in range(20)
            ]
        )
        trial_reservations = [
            item for item in results if item.source == "trial"
        ]
        self.assertEqual(
            len(trial_reservations),
            TRIAL_AI_REQUEST_LIMIT,
        )
        refreshed = await self.db.get_user_by_telegram_id(100)
        self.assertEqual(
            refreshed.trial_requests_used,
            TRIAL_AI_REQUEST_LIMIT,
        )
        self.assertFalse(refreshed.trial_active)
        self.assertEqual(refreshed.entitlement_plan, FREE)

    async def test_trial_expiration_ends_access(self) -> None:
        await self.db.activate_trial_once(100)
        expired = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        async with self.db._connect() as connection:
            await connection.execute(
                "UPDATE users SET trial_expires_at=? WHERE telegram_id=?",
                (expired, 100),
            )
            await connection.commit()
        user = await self.db.get_user_by_telegram_id(100)
        self.assertFalse(user.trial_active)
        self.assertFalse(
            has_assistant_access(user.plan, user.trial_active)
        )
        self.assertIn("Trial ended", trial_status_text(user, "en"))

    async def test_trial_unlocks_premium_and_assistants(self) -> None:
        activation = await self.db.activate_trial_once(100)
        user = activation.user
        self.assertTrue(
            has_premium_features(user.plan, user.trial_active)
        )
        self.assertTrue(
            has_assistant_access(user.plan, user.trial_active)
        )

    async def test_trial_migration_preserves_existing_user(self) -> None:
        async with self.db._connect() as connection:
            columns = {
                row[1]
                for row in await (
                    await connection.execute("PRAGMA table_info(users)")
                ).fetchall()
            }
        self.assertTrue(
            {
                "trial_granted",
                "trial_started_at",
                "trial_expires_at",
                "trial_requests_used",
                "trial_notification_sent",
            }.issubset(columns)
        )


class TrialNotificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_user_start_shows_trial_welcome(self) -> None:
        base_user = User(1, 7, FREE)
        active_user = User(
            1,
            7,
            FREE,
            trial_granted=True,
            trial_started_at=datetime.now(timezone.utc).isoformat(),
            trial_expires_at=(
                datetime.now(timezone.utc) + timedelta(hours=24)
            ).isoformat(),
            trial_notification_sent=True,
        )
        activation = SimpleNamespace(
            user=active_user,
            notification_required=True,
        )
        db = SimpleNamespace(
            register_user=AsyncMock(
                return_value=RegistrationResult(
                    base_user,
                    True,
                    False,
                )
            ),
            activate_trial_once=AsyncMock(return_value=activation),
        )
        message = SimpleNamespace(
            answer=AsyncMock(),
            from_user=SimpleNamespace(
                id=7,
                username="new",
                first_name="New",
                last_name=None,
                language_code="en",
            ),
        )
        await start_command(
            message,
            SimpleNamespace(args=None),
            db,
        )
        self.assertEqual(
            message.answer.await_args_list[0].args[0],
            new_user_trial_message("en"),
        )
        self.assertEqual(message.answer.await_count, 2)

    async def test_existing_user_gets_one_update_notification(self) -> None:
        middleware = UserProfileMiddleware()
        user = User(1, 42, FREE, language="en")
        activation = SimpleNamespace(
            user=User(
                1,
                42,
                FREE,
                language="en",
                trial_granted=True,
                trial_started_at=datetime.now(timezone.utc).isoformat(),
                trial_expires_at=(
                    datetime.now(timezone.utc) + timedelta(hours=24)
                ).isoformat(),
            ),
            notification_required=True,
        )
        db = SimpleNamespace(
            upsert_user=AsyncMock(return_value=user),
            activate_trial_once=AsyncMock(return_value=activation),
        )
        event = SimpleNamespace(
            text="hello",
            answer=AsyncMock(),
            from_user=SimpleNamespace(
                id=42,
                is_bot=False,
                username="user",
                first_name="User",
                last_name=None,
                language_code="en",
            ),
        )
        await middleware(AsyncMock(return_value="ok"), event, {"db": db})
        self.assertEqual(
            event.answer.await_args.args[0],
            existing_user_trial_message("en"),
        )

    async def test_callback_interaction_also_activates_trial(self) -> None:
        activation = SimpleNamespace(
            user=User(1, 42, FREE, language="ru"),
            notification_required=True,
        )
        db = SimpleNamespace(
            activate_trial_once=AsyncMock(return_value=activation)
        )
        event = SimpleNamespace(
            from_user=SimpleNamespace(id=42, language_code="ru"),
            message=SimpleNamespace(answer=AsyncMock()),
        )
        middleware = TrialCallbackMiddleware()
        with patch(
            "app.middlewares.Message",
            SimpleNamespace,
        ):
            await middleware(
                AsyncMock(return_value="ok"),
                event,
                {"db": db},
            )
        self.assertEqual(
            event.message.answer.await_args.args[0],
            existing_user_trial_message("ru"),
        )

    def test_trial_messages_are_localized(self) -> None:
        self.assertIn(
            "Добро пожаловать",
            new_user_trial_message("ru"),
        )
        self.assertIn(
            "Welcome",
            new_user_trial_message("en"),
        )
        self.assertIn(
            "15 AI-запросов",
            existing_user_trial_message("ru"),
        )
        self.assertIn(
            "15 AI requests",
            existing_user_trial_message("en"),
        )
