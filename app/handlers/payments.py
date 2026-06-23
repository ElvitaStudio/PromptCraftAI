from dataclasses import dataclass
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import Settings
from app.database import Database
from app.plans import PREMIUM, PREMIUM_PLUS, PREMIUM_PLUS_PRICE_STARS, PRO
from app.referrals import build_referral_link, invite_message


router = Router(name="payments")
CURRENCY = "XTR"


@dataclass(frozen=True, slots=True)
class PaidPlan:
    title: str
    description: str
    label: str
    amount: int


PLANS = {
    PRO: PaidPlan(
        "PromptCraft AI Pro",
        "PromptCraft AI Pro subscription for 30 days",
        "Pro 30 days",
        199,
    ),
    PREMIUM: PaidPlan(
        "PromptCraft AI Premium",
        "PromptCraft AI Premium subscription for 30 days",
        "Premium 30 days",
        399,
    ),
    PREMIUM_PLUS: PaidPlan(
        "PromptCraft AI Premium Plus",
        "PromptCraft AI Premium Plus subscription for 30 days",
        "Premium Plus 30 days",
        PREMIUM_PLUS_PRICE_STARS,
    ),
}


def build_payment_payload(
    plan: str,
    user_id: int,
    timestamp: int | None = None,
) -> str:
    if plan not in PLANS or user_id <= 0:
        raise ValueError("Invalid payment payload")
    stamp = int(time.time()) if timestamp is None else timestamp
    return f"plan:{plan}:{user_id}:{stamp}"


def parse_payment_payload(payload: str | None) -> tuple[str, int, int] | None:
    parts = (payload or "").split(":")
    if len(parts) != 4 or parts[0] != "plan" or parts[1] not in PLANS:
        return None
    try:
        user_id, stamp = int(parts[2]), int(parts[3])
    except ValueError:
        return None
    if user_id <= 0 or stamp <= 0:
        return None
    return parts[1], user_id, stamp


def _validate(payload: str, user_id: int, currency: str, amount: int) -> str | None:
    parsed = parse_payment_payload(payload)
    if not parsed:
        return None
    plan, owner_id, _ = parsed
    if owner_id != user_id or currency != CURRENCY or PLANS[plan].amount != amount:
        return None
    return plan


@router.callback_query(
    F.data.in_({"payment:pro", "payment:premium", "payment:premium_plus"})
)
async def send_invoice(callback: CallbackQuery, bot: Bot) -> None:
    plan = (callback.data or "").rsplit(":", 1)[-1]
    paid = PLANS[plan]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=paid.title,
        description=paid.description,
        payload=build_payment_payload(plan, callback.from_user.id),
        currency=CURRENCY,
        prices=[LabeledPrice(label=paid.label, amount=paid.amount)],
        provider_token="",
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, bot: Bot) -> None:
    valid = _validate(
        query.invoice_payload,
        query.from_user.id,
        query.currency,
        query.total_amount,
    )
    if valid:
        await bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=True,
        )
    else:
        await bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=False,
            error_message="Invalid payment",
        )


@router.message(F.successful_payment)
async def successful_payment(message: Message, db: Database) -> None:
    payment = message.successful_payment
    if not payment or not message.from_user:
        return
    plan = _validate(
        payment.invoice_payload,
        message.from_user.id,
        payment.currency,
        payment.total_amount,
    )
    if not plan:
        await message.answer("Invalid payment. Contact /paysupport")
        return
    await db.upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
        message.from_user.full_name,
    )
    processed = await db.process_stars_payment(
        message.from_user.id,
        plan,
        payment.currency,
        payment.total_amount,
        payment.invoice_payload,
        payment.telegram_payment_charge_id,
        payment.provider_payment_charge_id,
    )
    if processed:
        plan_name = PLANS[plan].title.removeprefix("PromptCraft AI ")
        await message.answer(
            f"✅ {plan_name} activated for 30 days."
        )
    else:
        await message.answer("ℹ️ Payment already processed.")


@router.message(Command("paysupport"))
async def pay_support(message: Message, settings: Settings) -> None:
    username = settings.support_username or "YOUR_SUPPORT_USERNAME"
    await message.answer(
        "💬 Payment support / Поддержка по оплате\n\n"
        f"@{username}\n\n"
        "Send your Telegram ID, plan and payment date."
    )


@router.callback_query(F.data == "payment:invite")
async def invite_callback(
    callback: CallbackQuery,
    db: Database,
    bot_username: str,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    if isinstance(callback.message, Message):
        await callback.message.answer(
            invite_message(
                build_referral_link(bot_username, user.telegram_id),
                user.language or "ru",
            )
        )
    await callback.answer()
