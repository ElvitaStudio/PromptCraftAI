from openai import AsyncOpenAI

from app.catalog import AI_MODELS, CATEGORIES


class OpenAIService:
    def __init__(self, api_key: str, generation_model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.generation_model = generation_model

    async def generate_prompt(
        self,
        task: str,
        category: str,
        target_ai: str,
        language: str,
        expert: bool = False,
        variants: int = 1,
    ) -> str:
        if category not in CATEGORIES or target_ai not in AI_MODELS:
            raise ValueError("Unsupported category or AI")
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported language")
        variants = max(1, min(variants, 3))
        output_language = "English" if language == "en" else "Russian"
        mode = (
            "Use Expert mode with role, context, constraints, output schema, "
            "quality criteria and edge cases."
            if expert
            else "Create a clear, practical, production-ready prompt."
        )
        instructions = f"""
You are PromptCraft AI, a senior prompt engineer.
Create a prompt for {AI_MODELS[target_ai]} in category
{CATEGORIES[category]["en"]}. Write it in {output_language}.
{mode}
Generate {variants} distinct variant(s). Preserve the user's intent.
Never answer the task itself. Return only the ready-to-copy prompt.
For multiple variants, label them clearly in the selected language.
""".strip()
        return await self._generate(instructions, task)

    async def improve_prompt(
        self,
        prompt: str,
        target_ai: str,
        language: str,
    ) -> str:
        if target_ai not in AI_MODELS:
            raise ValueError("Unsupported AI")
        output_language = "English" if language == "en" else "Russian"
        instructions = f"""
Improve this prompt for {AI_MODELS[target_ai]} in {output_language}.
Make it precise, structured, actionable and unambiguous. Add useful context,
constraints and output format without changing the goal. Return only the
improved prompt.
""".strip()
        return await self._generate(instructions, prompt)

    async def transform_prompt(
        self,
        action: str,
        prompt: str,
        target_ai: str,
        language: str,
        source_text: str = "",
    ) -> str:
        if target_ai not in AI_MODELS:
            raise ValueError("Unsupported AI")
        output_language = "English" if language == "en" else "Russian"
        actions = {
            "shorter": (
                "Make the prompt significantly shorter while preserving its "
                "goal, essential constraints and output format."
            ),
            "details": (
                "Expand the prompt with useful context, explicit steps, "
                "constraints, quality criteria and a clear output format."
            ),
            "translate_en": (
                "Translate the prompt into natural professional English. "
                "Preserve every instruction and constraint."
            ),
            "variant": (
                "Create a substantially different alternative prompt for the "
                "same original task. Keep the goal but change the structure "
                "and prompt-engineering approach."
            ),
        }
        instruction = actions.get(action)
        if instruction is None:
            raise ValueError("Unsupported prompt action")
        result_language = "English" if action == "translate_en" else output_language
        instructions = f"""
You are a senior prompt engineer.
The target AI is {AI_MODELS[target_ai]}.
{instruction}
Return only the ready-to-copy prompt in {result_language}.
Do not answer the prompt itself.
Original user request, when available: {source_text}
""".strip()
        return await self._generate(instructions, prompt)

    async def _generate(self, instructions: str, text: str) -> str:
        response = await self.client.responses.create(
            model=self.generation_model,
            instructions=instructions,
            input=text,
        )
        result = response.output_text.strip()
        if not result:
            raise ValueError("OpenAI returned an empty result")
        return result
