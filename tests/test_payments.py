from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from app.handlers.payments import (
    build_payment_payload,
    parse_payment_payload,
    pre_checkout,
    send_invoice,
)


class PaymentTests(unittest.IsolatedAsyncioTestCase):
    def test_payload_parser(self) -> None:
        self.assertEqual(
            parse_payment_payload("plan:pro:123:1700000000"),
            ("pro", 123, 1700000000),
        )
        self.assertIsNone(parse_payment_payload("bad"))

    async def test_pro_invoice(self) -> None:
        callback = SimpleNamespace(
            data="payment:pro",
            from_user=SimpleNamespace(id=123),
            answer=AsyncMock(),
        )
        bot = SimpleNamespace(send_invoice=AsyncMock())
        with patch("app.handlers.payments.time.time", return_value=1700000000):
            await send_invoice(callback, bot)
        kwargs = bot.send_invoice.await_args.kwargs
        self.assertEqual(kwargs["currency"], "XTR")
        self.assertEqual(kwargs["provider_token"], "")
        self.assertEqual(kwargs["prices"][0].amount, 199)

    async def test_premium_invoice(self) -> None:
        callback = SimpleNamespace(
            data="payment:premium",
            from_user=SimpleNamespace(id=123),
            answer=AsyncMock(),
        )
        bot = SimpleNamespace(send_invoice=AsyncMock())
        await send_invoice(callback, bot)
        self.assertEqual(
            bot.send_invoice.await_args.kwargs["prices"][0].amount,
            399,
        )

    async def test_pre_checkout_validation(self) -> None:
        bot = SimpleNamespace(answer_pre_checkout_query=AsyncMock())
        valid = SimpleNamespace(
            id="1",
            from_user=SimpleNamespace(id=123),
            invoice_payload=build_payment_payload(
                "pro", 123, 1700000000
            ),
            currency="XTR",
            total_amount=199,
        )
        await pre_checkout(valid, bot)
        self.assertTrue(bot.answer_pre_checkout_query.await_args.kwargs["ok"])

        invalid = SimpleNamespace(
            id="2",
            from_user=SimpleNamespace(id=999),
            invoice_payload=valid.invoice_payload,
            currency="XTR",
            total_amount=199,
        )
        await pre_checkout(invalid, bot)
        self.assertFalse(bot.answer_pre_checkout_query.await_args.kwargs["ok"])
