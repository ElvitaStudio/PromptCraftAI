from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.catalog import tr
from app.database import Database
from app.keyboards import prompt_actions_keyboard, prompt_chat_ai_keyboard
from app.plans import get_plan_limits, has_premium_features
from app.presentation import prompt_result_chunks
from app.services.openai_service import OpenAIService


router = Router(name="prompt_chat")
logger = logging.getLogger(__name__)


class PromptChatFlow(StatesGroup):
    idea = State()
    project_language = State()
    audience = State()
    features = State()
    design = State()
    monetization = State()
    technologies = State()


QUESTIONS = {
    "idea": (
        "💬 Опишите вашу идею одним или несколькими предложениями.",
        "💬 Describe your idea in one or more sentences.",
    ),
    "project_language": (
        "1/6 🌐 На каком языке должен работать проект или интерфейс?",
        "1/6 🌐 What language should the project or interface use?",
    ),
    "audience": (
        "2/6 👥 Для кого создаётся проект?",
        "2/6 👥 Who is the project for?",
    ),
    "features": (
        "3/6 🧩 Какие основные функции нужны?",
        "3/6 🧩 What core features are required?",
    ),
    "design": (
        "4/6 🎨 Нужен ли дизайн? Опишите стиль и пожелания.",
        "4/6 🎨 Is design required? Describe the desired style.",
    ),
    "monetization": (
        "5/6 💳 Нужна ли монетизация? Если да, какая?",
        "5/6 💳 Is monetization required? If yes, what kind?",
    ),
    "technologies": (
        "6/6 🛠 Какие технологии или ограничения нужно учесть?",
        "6/6 🛠 Which technologies or constraints should be considered?",
    ),
}


async def _start_chat(message: Message, language: str, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PromptChatFlow.idea)
    await state.update_data(chat_language=language)
    await message.answer(
        tr(
            language,
            "💬 Prompt Chat\n\n"
            "Я задам несколько коротких вопросов и соберу максимально "
            "качественный профессиональный промпт.\n\n"
            + QUESTIONS["idea"][0],
            "💬 Prompt Chat\n\n"
            "I will ask a few short questions and build a high-quality "
            "professional prompt.\n\n"
            + QUESTIONS["idea"][1],
        )
    )


@router.message(Command("chat"))
async def prompt_chat_command(
    message: Message,
    db: Database,
    state: FSMContext,
) -> None:
    if not message.from_user:
        return
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if user:
        await _start_chat(message, user.language or "ru", state)


@router.callback_query(F.data == "promptchat:start")
async def prompt_chat_start(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user and isinstance(callback.message, Message):
        await _start_chat(callback.message, user.language or "ru", state)
    await callback.answer()


async def _capture(
    message: Message,
    state: FSMContext,
    key: str,
    next_state,
    next_question: str,
) -> None:
    if not message.text:
        return
    data = await state.get_data()
    language = data.get("chat_language", "ru")
    await state.update_data(**{key: message.text})
    await state.set_state(next_state)
    question = QUESTIONS[next_question]
    await message.answer(question[1] if language == "en" else question[0])


@router.message(PromptChatFlow.idea, F.text)
async def chat_idea(message: Message, state: FSMContext) -> None:
    await _capture(
        message, state, "idea",
        PromptChatFlow.project_language, "project_language",
    )


@router.message(PromptChatFlow.project_language, F.text)
async def chat_project_language(message: Message, state: FSMContext) -> None:
    await _capture(
        message, state, "project_language",
        PromptChatFlow.audience, "audience",
    )


@router.message(PromptChatFlow.audience, F.text)
async def chat_audience(message: Message, state: FSMContext) -> None:
    await _capture(
        message, state, "audience",
        PromptChatFlow.features, "features",
    )


@router.message(PromptChatFlow.features, F.text)
async def chat_features(message: Message, state: FSMContext) -> None:
    await _capture(
        message, state, "features",
        PromptChatFlow.design, "design",
    )


@router.message(PromptChatFlow.design, F.text)
async def chat_design(message: Message, state: FSMContext) -> None:
    await _capture(
        message, state, "design",
        PromptChatFlow.monetization, "monetization",
    )


@router.message(PromptChatFlow.monetization, F.text)
async def chat_monetization(message: Message, state: FSMContext) -> None:
    await _capture(
        message, state, "monetization",
        PromptChatFlow.technologies, "technologies",
    )


@router.message(PromptChatFlow.technologies, F.text)
async def chat_technologies(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    data = await state.get_data()
    language = data.get("chat_language", "ru")
    await state.update_data(technologies=message.text)
    await message.answer(
        tr(
            language,
            "🤖 Какой AI будет выполнять задачу?",
            "🤖 Which AI will execute the task?",
        ),
        reply_markup=prompt_chat_ai_keyboard(language),
    )


@router.callback_query(F.data.startswith("promptchat:ai:"))
async def finish_prompt_chat(
    callback: CallbackQuery,
    db: Database,
    openai_service: OpenAIService,
    state: FSMContext,
) -> None:
    target_ai = (callback.data or "").rsplit(":", 1)[-1]
    supported = {
        "claude_code", "codex", "cursor",
        "chatgpt", "gemini", "deepseek",
    }
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        target_ai not in supported
        or not user
        or not user.language
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid AI", show_alert=True)
        return
    data = await state.get_data()
    required = {
        "idea", "project_language", "audience", "features",
        "design", "monetization", "technologies",
    }
    if not required.issubset(data):
        await callback.answer(
            tr(
                user.language,
                "Сначала ответьте на все вопросы",
                "Please answer all questions first",
            ),
            show_alert=True,
        )
        return
    if not await db.reserve_request(user):
        await callback.answer(
            tr(
                user.language,
                "Лимит запросов исчерпан",
                "Request limit reached",
            ),
            show_alert=True,
        )
        return
    await callback.answer()
    status = await callback.message.answer(
        tr(
            user.language,
            "🧠 Собираю профессиональный промпт…",
            "🧠 Building your professional prompt…",
        )
    )
    difficulty = user.last_difficulty
    if difficulty == "expert" and not has_premium_features(user.plan):
        difficulty = "advanced"
    variants = get_plan_limits(user.plan).response_variants
    try:
        result = await openai_service.generate_prompt_chat(
            {key: str(data[key]) for key in required},
            target_ai,
            user.language,
            difficulty=difficulty,
            response_style=user.last_response_style,
            variants=variants,
        )
        prompt_id = await db.save_prompt(
            user.id,
            "code",
            target_ai,
            str(data["idea"]),
            result,
            f"prompt_chat:{difficulty}:{user.last_response_style}",
            user.language,
        )
        chunks = prompt_result_chunks(result, user.language)
        if len(chunks) == 1:
            await status.edit_text(
                chunks[0],
                reply_markup=prompt_actions_keyboard(prompt_id, user.language),
            )
        else:
            await status.edit_text(chunks[0])
            for chunk in chunks[1:-1]:
                await callback.message.answer(chunk)
            await callback.message.answer(
                chunks[-1],
                reply_markup=prompt_actions_keyboard(prompt_id, user.language),
            )
        await state.clear()
    except Exception:
        logger.exception("Prompt Chat failed for user %s", user.telegram_id)
        await db.release_request(user)
        await status.edit_text(
            tr(
                user.language,
                "Не удалось создать промпт. Попробуйте позже.",
                "Could not create the prompt. Try again later.",
            )
        )
