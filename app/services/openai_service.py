from openai import AsyncOpenAI

from app.catalog import AI_MODELS, CATEGORIES
from app.prompt_engineering import build_generation_instructions

TARGET_AI_NAMES = {**AI_MODELS, "deepseek": "DeepSeek"}


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
        difficulty: str | None = None,
        response_style: str = "professional",
        workflow: str = "create",
    ) -> str:
        if category not in CATEGORIES or target_ai not in AI_MODELS:
            raise ValueError("Unsupported category or AI")
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported language")
        variants = max(1, min(variants, 3))
        selected_difficulty = difficulty or (
            "expert" if expert else "simple"
        )
        instructions = build_generation_instructions(
            category,
            target_ai,
            language,
            selected_difficulty,
            response_style,
            variants,
            workflow,
        )
        return await self._generate(instructions, task)

    async def optimize_prompt(
        self,
        prompt: str,
        category: str,
        target_ai: str,
        language: str,
        difficulty: str = "advanced",
        response_style: str = "professional",
        variants: int = 1,
    ) -> str:
        return await self.generate_prompt(
            task=prompt,
            category=category,
            target_ai=target_ai,
            language=language,
            variants=variants,
            difficulty=difficulty,
            response_style=response_style,
            workflow="optimize",
        )

    async def generate_prompt_chat(
        self,
        requirements: dict[str, str],
        target_ai: str,
        language: str,
        difficulty: str = "advanced",
        response_style: str = "professional",
        variants: int = 1,
    ) -> str:
        supported = {
            "claude_code": "Claude Code",
            "codex": "Codex",
            "cursor": "Cursor",
            "chatgpt": "ChatGPT",
            "gemini": "Gemini",
            "deepseek": "DeepSeek",
        }
        if target_ai not in supported:
            raise ValueError("Unsupported Prompt Chat AI")
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported language")
        variants = max(1, min(variants, 3))
        output_language = "English" if language == "en" else "Russian"
        instructions = f"""
You are PromptCraft AI, a senior requirements analyst and prompt engineer.
Turn the completed discovery interview into a production-ready prompt for
{supported[target_ai]}.

Output language: {output_language}
Difficulty: {difficulty}
Response style: {response_style}
Variants: {variants}

The final prompt must include:
- specialist role and project goal;
- audience and user context;
- functional requirements and priorities;
- design and UX expectations;
- monetization requirements;
- technology stack and versions;
- architecture and project structure;
- constraints, assumptions and non-goals;
- security, validation and error handling;
- testing strategy and acceptance criteria;
- documentation and deployment expectations;
- exact response format for the target AI.

For Claude Code, Codex and Cursor, require repository inspection, minimal
coherent edits, changed-file reporting and relevant test execution.
Do not solve the project. Return only the ready-to-copy professional prompt.
Do not invent missing facts; use explicit placeholders where necessary.
""".strip()
        interview = "\n".join(
            f"{key}: {value}" for key, value in requirements.items()
        )
        return await self._generate(instructions, interview)

    async def improve_prompt(
        self,
        prompt: str,
        target_ai: str,
        language: str,
    ) -> str:
        if target_ai not in TARGET_AI_NAMES:
            raise ValueError("Unsupported AI")
        output_language = "English" if language == "en" else "Russian"
        instructions = f"""
Improve this prompt for {TARGET_AI_NAMES[target_ai]} in {output_language}.
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
        if target_ai not in TARGET_AI_NAMES:
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
The target AI is {TARGET_AI_NAMES[target_ai]}.
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
