import unittest

from app.services.openai_service import OpenAIService


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Response", (), {"output_text": " Ready prompt "})()


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class OpenAIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_prompt_targets_selected_ai(self) -> None:
        service = object.__new__(OpenAIService)
        service.client = FakeClient()
        service.generation_model = "test-model"
        result = await service.generate_prompt(
            "Build an API",
            "code",
            "codex",
            "en",
            expert=True,
            variants=3,
        )
        self.assertEqual(result, "Ready prompt")
        kwargs = service.client.responses.kwargs
        self.assertEqual(kwargs["model"], "test-model")
        self.assertIn("Codex", kwargs["instructions"])
        self.assertIn("Expert mode", kwargs["instructions"])
        self.assertIn("3 distinct", kwargs["instructions"])

    async def test_improve_prompt(self) -> None:
        service = object.__new__(OpenAIService)
        service.client = FakeClient()
        service.generation_model = "test-model"
        result = await service.improve_prompt("draft", "claude", "ru")
        self.assertEqual(result, "Ready prompt")
        self.assertIn(
            "Claude",
            service.client.responses.kwargs["instructions"],
        )

    async def test_invalid_target_is_rejected(self) -> None:
        service = object.__new__(OpenAIService)
        with self.assertRaises(ValueError):
            await service.generate_prompt(
                "task", "text", "unknown", "ru"
            )

    async def test_transform_actions_are_supported(self) -> None:
        service = object.__new__(OpenAIService)
        service.client = FakeClient()
        service.generation_model = "test-model"
        for action in ("shorter", "details", "translate_en", "variant"):
            with self.subTest(action=action):
                result = await service.transform_prompt(
                    action,
                    "prompt",
                    "chatgpt",
                    "ru",
                    "source",
                )
                self.assertEqual(result, "Ready prompt")
