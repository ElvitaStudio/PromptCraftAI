from __future__ import annotations

from app.catalog import AI_MODELS, CATEGORIES
from app.prompt_profiles import CODING_ASSISTANTS, DIFFICULTIES, RESPONSE_STYLES


DIFFICULTY_GUIDANCE = {
    "simple": (
        "Keep the prompt approachable and focused. Include the minimum context "
        "and constraints needed for a reliable result."
    ),
    "advanced": (
        "Create an advanced production-ready prompt with explicit context, "
        "steps, constraints, quality checks and acceptance criteria."
    ),
    "expert": (
        "Use Expert mode. Surface assumptions, edge cases, failure modes, "
        "trade-offs, verification steps and a strict output schema."
    ),
}

STYLE_GUIDANCE = {
    "short": (
        "Keep the final prompt concise. Use compact sections and remove all "
        "nonessential commentary."
    ),
    "concise": (
        "Keep the final prompt concise, direct and information-dense. Preserve "
        "essential constraints while avoiding repetition."
    ),
    "detailed": (
        "Make the final prompt detailed, explanatory and comprehensive."
    ),
    "professional": (
        "Use a precise professional tone, clear headings and measurable "
        "quality criteria."
    ),
    "expert": (
        "Write for an expert operator. Use domain terminology, rigorous "
        "reasoning instructions and explicit evaluation criteria."
    ),
    "creative": (
        "Use an original, engaging prompt structure and encourage thoughtful "
        "alternatives without weakening precision or constraints."
    ),
}

CATEGORY_GUIDANCE = {
    "text": (
        "Define audience, purpose, tone, source material, structure, length, "
        "facts policy and final format."
    ),
    "images": (
        "Define subject, environment, composition, visual style, lighting, "
        "color, lens/camera, aspect ratio, detail level and exclusions."
    ),
    "video": (
        "Define narrative, shot sequence, subject motion, camera movement, "
        "lighting, timing, sound, continuity, aspect ratio and artifacts to avoid."
    ),
    "code": (
        "The prompt MUST contain these explicit sections: Role of the specialist; "
        "Goal; Stack and versions; Functional and non-functional requirements; "
        "Project structure; Constraints; Required response format; Tests; Error "
        "handling; Documentation; Acceptance criteria."
    ),
    "marketing": (
        "Define product, audience, insight, offer, funnel stage, channel, tone, "
        "proof, CTA, restrictions, variants and success metrics."
    ),
    "business": (
        "Define business context, stakeholders, objective, available data, "
        "constraints, risks, decision criteria, deliverables and next actions."
    ),
    "study": (
        "Define learner level, learning objective, prerequisites, explanation "
        "method, examples, exercises, misconceptions and knowledge checks."
    ),
}

AI_GUIDANCE = {
    "claude_code": (
        "Optimize specifically for Claude Code: instruct it to inspect the "
        "repository before editing, identify affected files, make minimal "
        "coherent changes, preserve existing behavior, run relevant tests and "
        "summarize changed files and verification."
    ),
    "codex": (
        "Optimize specifically for Codex: provide repository context, concrete "
        "implementation scope, file-level expectations, constraints, safe tool "
        "usage, test commands and a concise completion report."
    ),
    "cursor": (
        "Optimize specifically for Cursor: identify files and symbols to inspect, "
        "state coding conventions, request incremental edits, prevent unrelated "
        "rewrites and require diagnostics plus tests."
    ),
    "midjourney": (
        "Use natural visual language followed by appropriate Midjourney "
        "parameters. Do not add unsupported parameters."
    ),
    "gpt_image": (
        "Describe exact visual content, composition and any in-image text "
        "verbatim. Include edit/preservation constraints when relevant."
    ),
    "flux": (
        "Prioritize descriptive visual tokens, spatial relationships, materials, "
        "lighting and negative constraints."
    ),
    "kling": (
        "Specify start frame, temporal action, camera motion, duration and motion "
        "consistency."
    ),
    "veo": (
        "Specify cinematic sequence, camera, sound, dialogue, timing and scene "
        "continuity."
    ),
    "runway": (
        "Specify subject motion, camera motion, transformation timing and visual "
        "elements that must remain stable."
    ),
}


def build_generation_instructions(
    category: str,
    target_ai: str,
    language: str,
    difficulty: str,
    response_style: str,
    variants: int,
    workflow: str,
) -> str:
    if category not in CATEGORIES or target_ai not in AI_MODELS:
        raise ValueError("Unsupported category or AI")
    if difficulty not in DIFFICULTIES:
        raise ValueError("Unsupported difficulty")
    if response_style not in RESPONSE_STYLES:
        raise ValueError("Unsupported response style")
    if workflow not in {"create", "optimize"}:
        raise ValueError("Unsupported workflow")

    output_language = "English" if language == "en" else "Russian"
    action = (
        "Transform the user's weak or incomplete draft into a substantially "
        "stronger professional prompt. Preserve its actual goal."
        if workflow == "optimize"
        else "Create a strong professional prompt from the user's task."
    )
    ai_specific = AI_GUIDANCE.get(
        target_ai,
        (
            f"Adapt the structure and instruction style to "
            f"{AI_MODELS[target_ai]}'s strengths."
        ),
    )
    code_rule = ""
    if category == "code" or target_ai in CODING_ASSISTANTS:
        code_rule = (
            "\nThis is a software-engineering prompt. Even when details are "
            "missing, include clearly marked placeholders rather than inventing "
            "requirements. Require implementation, tests, error handling and "
            "documentation."
        )

    return f"""
You are PromptCraft AI, a senior prompt engineer and domain specialist.
{action}

Target AI: {AI_MODELS[target_ai]}
Category: {CATEGORIES[category]["en"]}
Output language: {output_language}
Difficulty: {difficulty}
Response style: {response_style}

Difficulty requirements:
{DIFFICULTY_GUIDANCE[difficulty]}

Style requirements:
{STYLE_GUIDANCE[response_style]}

Category blueprint:
{CATEGORY_GUIDANCE[category]}

Target-AI guidance:
{ai_specific}
{code_rule}

Generate {variants} distinct variant(s). Preserve the user's intent.
Return only the ready-to-copy prompt, never the answer to that prompt.
Use descriptive section headings inside the generated prompt.
For multiple variants, label them clearly in {output_language}.
Do not claim access to files, tools, facts or context that was not provided.
""".strip()
