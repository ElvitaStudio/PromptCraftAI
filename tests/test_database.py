import asyncio
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.database import Database
from app.plans import FREE, PREMIUM, PRO


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "test.db")
        await self.db.initialize()
        self.user = await self.db.upsert_user(
            100, "tester", "Test", "User", "Test User"
        )

    async def asyncTearDown(self) -> None:
        self.temp.cleanup()

    async def test_language_is_persisted(self) -> None:
        await self.db.set_language(100, "en")
        user = await self.db.get_user_by_telegram_id(100)
        self.assertEqual(user.language, "en")

    async def test_free_request_limit(self) -> None:
        for _ in range(5):
            self.assertTrue(await self.db.reserve_request(self.user))
        self.assertFalse(await self.db.reserve_request(self.user))
        usage = await self.db.get_request_usage(self.user)
        self.assertEqual((usage.used, usage.remaining), (5, 0))

    async def test_request_reservation_is_atomic(self) -> None:
        results = await asyncio.gather(
            *[self.db.reserve_request(self.user) for _ in range(8)]
        )
        self.assertEqual(results.count(True), 5)

    async def test_free_improvement_limit(self) -> None:
        self.assertTrue(await self.db.reserve_improvement(self.user))
        self.assertFalse(await self.db.reserve_improvement(self.user))

    async def test_pro_request_limit(self) -> None:
        await self.db.set_admin_user_plan(self.user.id, PRO)
        user = await self.db.get_user_by_telegram_id(100)
        self.assertEqual(user.plan, PRO)
        for _ in range(100):
            self.assertTrue(await self.db.reserve_request(user))
        self.assertFalse(await self.db.reserve_request(user))

    async def test_premium_is_unlimited(self) -> None:
        await self.db.set_admin_user_plan(self.user.id, PREMIUM)
        user = await self.db.get_user_by_telegram_id(100)
        self.assertTrue(await self.db.reserve_request(user))
        usage = await self.db.get_request_usage(user)
        self.assertIsNone(usage.limit)

    async def test_blocked_user_cannot_reserve(self) -> None:
        await self.db.set_user_blocked(self.user.id, True)
        user = await self.db.get_user_by_telegram_id(100)
        self.assertTrue(user.is_blocked)
        self.assertFalse(await self.db.reserve_request(user))

    async def test_prompt_history_follows_plan(self) -> None:
        for index in range(40):
            await self.db.save_prompt(
                self.user.id,
                "text",
                "chatgpt",
                f"source {index}",
                f"prompt {index}",
                "standard",
            )
        self.assertEqual(len(await self.db.get_prompt_history(self.user)), 5)
        await self.db.set_admin_user_plan(self.user.id, PRO)
        pro = await self.db.get_user_by_telegram_id(100)
        self.assertEqual(len(await self.db.get_prompt_history(pro)), 30)

    async def test_history_preserves_all_prompt_metadata(self) -> None:
        prompt_id = await self.db.save_prompt(
            self.user.id,
            "images",
            "midjourney",
            "original request",
            "final prompt",
            "expert",
            "en",
        )
        record = await self.db.get_prompt(prompt_id, self.user.id)
        self.assertEqual(record.source_text, "original request")
        self.assertEqual(record.prompt_text, "final prompt")
        self.assertEqual(record.category, "images")
        self.assertEqual(record.target_ai, "midjourney")
        self.assertEqual(record.language, "en")
        self.assertTrue(record.created_at)

    async def test_referral_rewards_once(self) -> None:
        first = await self.db.register_user(
            200, "friend", "Friend",
            referred_by_telegram_id=100,
        )
        second = await self.db.register_user(
            200, "friend", "Friend",
            referred_by_telegram_id=100,
        )
        self.assertTrue(first.referral_rewarded)
        self.assertFalse(second.referral_rewarded)
        inviter = await self.db.get_user_by_telegram_id(100)
        self.assertEqual(inviter.plan, PREMIUM)
        self.assertEqual(await self.db.get_referral_count(self.user.id), 1)

    async def test_self_referral_is_rejected(self) -> None:
        result = await self.db.register_user(
            300, "self", "Self", referred_by_telegram_id=300
        )
        self.assertFalse(result.referral_rewarded)

    async def test_payment_is_idempotent(self) -> None:
        kwargs = dict(
            telegram_id=100,
            plan=PRO,
            currency="XTR",
            amount=199,
            payload="plan:pro:100:1700000000",
            telegram_payment_charge_id="charge-1",
            provider_payment_charge_id="",
        )
        self.assertTrue(await self.db.process_stars_payment(**kwargs))
        first = await self.db.get_user_by_telegram_id(100)
        self.assertFalse(await self.db.process_stars_payment(**kwargs))
        second = await self.db.get_user_by_telegram_id(100)
        self.assertEqual(first.plan_until, second.plan_until)
        payment = await self.db.get_payment_by_charge_id("charge-1")
        self.assertEqual(payment.amount, 199)

    async def test_admin_search_and_stats(self) -> None:
        await self.db.upsert_user(222, "search_me", "Search")
        page = await self.db.get_admin_users_page(0, search="search_me")
        self.assertEqual(page.total_users, 1)
        page = await self.db.get_admin_users_page(0, search="222")
        self.assertEqual(page.users[0].telegram_id, 222)
        stats = await self.db.get_admin_statistics()
        self.assertEqual(stats.total_users, 2)

    async def test_plan_expiration_is_future(self) -> None:
        await self.db.process_stars_payment(
            100, PRO, "XTR", 199, "payload", "charge-future", ""
        )
        user = await self.db.get_user_by_telegram_id(100)
        self.assertGreater(
            datetime.fromisoformat(user.plan_until),
            datetime.now(timezone.utc),
        )
