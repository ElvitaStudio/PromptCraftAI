import unittest

from app.plans import FREE, PREMIUM, PRO, get_plan_limits


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
