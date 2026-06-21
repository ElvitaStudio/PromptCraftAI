import unittest

from app.referrals import (
    build_referral_link,
    invite_message,
    parse_referral_payload,
)


class ReferralTests(unittest.TestCase):
    def test_link_and_payload(self) -> None:
        self.assertEqual(
            build_referral_link("@PromptCraftBot", 42),
            "https://t.me/PromptCraftBot?start=ref_42",
        )
        self.assertEqual(parse_referral_payload("ref_42"), 42)
        self.assertIsNone(parse_referral_payload("ref_bad"))

    def test_invite_message_languages(self) -> None:
        self.assertIn("Пригласите", invite_message("link", "ru"))
        self.assertIn("Invite", invite_message("link", "en"))
