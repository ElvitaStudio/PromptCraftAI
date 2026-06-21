from datetime import datetime, timezone
import unittest

from app.database import PromptRecord
from app.history import history_chunks


class HistoryTests(unittest.TestCase):
    def test_empty_history_is_bilingual(self) -> None:
        self.assertIn("пустая", history_chunks([], "ru")[0])
        self.assertIn("empty", history_chunks([], "en")[0])

    def test_history_contains_prompt(self) -> None:
        record = PromptRecord(
            1, 1, "text", "chatgpt", "source", "ready prompt",
            "standard", datetime.now(timezone.utc).isoformat(),
        )
        text = history_chunks([record], "en")[0]
        self.assertIn("ChatGPT", text)
        self.assertIn("ready prompt", text)
