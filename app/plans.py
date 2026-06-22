from dataclasses import dataclass

FREE = "free"
PRO = "pro"
PREMIUM = "premium"
PREMIUM_PLUS = "premium_plus"
PREMIUM_PLUS_PRICE_STARS = 2499
VALID_PLANS = {FREE, PRO, PREMIUM, PREMIUM_PLUS}


@dataclass(frozen=True, slots=True)
class PlanLimits:
    name: str
    requests_daily_limit: int | None
    history_limit: int
    improvements_daily_limit: int | None
    expert_mode: bool
    response_variants: int


PLAN_LIMITS = {
    FREE: PlanLimits("Free", 5, 5, 1, False, 1),
    PRO: PlanLimits("Pro", 100, 30, None, False, 2),
    PREMIUM: PlanLimits("Premium", None, 100, None, True, 3),
    PREMIUM_PLUS: PlanLimits("Premium Plus", None, 100, None, True, 3),
}


def get_plan_limits(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[FREE])


def has_premium_features(plan: str) -> bool:
    return plan in {PREMIUM, PREMIUM_PLUS}


def has_assistant_access(plan: str) -> bool:
    return plan == PREMIUM_PLUS
