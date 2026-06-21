import unittest

from app.plans import (
    FREE,
    PREMIUM,
    PREMIUM_PLUS,
    PREMIUM_PLUS_PRICE_STARS,
    PRO,
    get_plan_limits,
    has_assistant_access,
    has_premium_features,
)


class PlanTests(unittest.TestCase):
    def test_free(self) -> None:
        plan = get_plan_limits(FREE)
        self.assertEqual(plan.requests_daily_limit, 5)
        self.assertEqual(plan.history_limit, 5)
        self.assertEqual(plan.improvements_daily_limit, 1)

    def test_pro(self) -> None:
        plan = get_plan_limits(PRO)
        self.assertEqual(plan.requests_daily_limit, 100)
        self.assertEqual(plan.history_limit, 30)
        self.assertEqual(plan.response_variants, 2)

    def test_premium(self) -> None:
        plan = get_plan_limits(PREMIUM)
        self.assertIsNone(plan.requests_daily_limit)
        self.assertTrue(plan.expert_mode)
        self.assertEqual(plan.response_variants, 3)

    def test_premium_plus(self) -> None:
        plan = get_plan_limits(PREMIUM_PLUS)
        self.assertTrue(plan.expert_mode)
        self.assertTrue(has_premium_features(PREMIUM_PLUS))
        self.assertTrue(has_assistant_access(PREMIUM_PLUS))
        self.assertFalse(has_assistant_access(PREMIUM))
        self.assertGreater(PREMIUM_PLUS_PRICE_STARS, 0)
