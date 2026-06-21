import unittest

from app.admin import dashboard_text, user_card_text
from app.admin_keyboards import dashboard_keyboard, user_card_keyboard
from app.database import AdminStatistics, AdminUser


class AdminTests(unittest.TestCase):
    def test_dashboard_metrics(self) -> None:
        stats = AdminStatistics(10, 5, 3, 2, 4, 997, 3, 1, 50, 8)
        text = dashboard_text(stats)
        self.assertIn("Доход: 997 Stars", text)
        self.assertIn("Продаж Pro: 3", text)
        callbacks = {
            button.callback_data
            for row in dashboard_keyboard().inline_keyboard
            for button in row
        }
        self.assertIn("admin:search", callbacks)

    def test_user_card_and_block_button(self) -> None:
        user = AdminUser(
            1, 123, None, "No", "Username", "No Username", "ru",
            "free", None, None, False, "2026-01-01T00:00:00+00:00",
        )
        self.assertIn("Username: —", user_card_text(user))
        callbacks = {
            button.callback_data
            for row in user_card_keyboard(user, 0).inline_keyboard
            for button in row
        }
        self.assertIn("admin:block:1:0:-", callbacks)
