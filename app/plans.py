from dataclasses import dataclass

FREE = "free"
PRO = "pro"
PREMIUM = "premium"
VALID_PLANS = {FREE, PRO, PREMIUM}


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
}


def get_plan_limits(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[FREE])
