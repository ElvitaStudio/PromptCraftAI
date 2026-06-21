import unittest

from app.catalog import AI_MODELS, CATEGORIES, LANGUAGES
from app.keyboards import (
    ai_models_keyboard,
    categories_keyboard,
    language_keyboard,
    premium_keyboard,
)


class CatalogTests(unittest.TestCase):
    def test_languages(self) -> None:
        self.assertEqual(set(LANGUAGES), {"ru", "en"})
        callbacks = [
            button.callback_data
            for row in language_keyboard().inline_keyboard
            for button in row
        ]
        self.assertEqual(callbacks, ["language:ru", "language:en"])

    def test_all_categories_are_available(self) -> None:
        self.assertEqual(
            set(CATEGORIES),
            {"text", "images", "video", "code", "marketing", "business", "study"},
        )
        callbacks = {
            button.callback_data
            for row in categories_keyboard("ru").inline_keyboard
            for button in row
        }
        self.assertEqual(
            callbacks,
            {f"category:{category}" for category in CATEGORIES},
        )

    def test_all_ai_models_are_available(self) -> None:
        self.assertEqual(len(AI_MODELS), 13)
        callbacks = {
            button.callback_data
            for row in ai_models_keyboard("code").inline_keyboard
            for button in row
        }
        self.assertTrue(
            {f"ai:code:{model}" for model in AI_MODELS}.issubset(callbacks)
        )

    def test_paid_plan_buttons(self) -> None:
        buttons = [
            (button.text, button.callback_data)
            for row in premium_keyboard().inline_keyboard
            for button in row
        ]
        self.assertEqual(buttons[0], ("⭐ Pro — 199 Stars", "payment:pro"))
        self.assertEqual(
            buttons[1],
            ("👑 Premium — 399 Stars", "payment:premium"),
        )
