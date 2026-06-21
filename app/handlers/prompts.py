from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.catalog import AI_MODELS, CATEGORIES, tr
from app.database import Database
from app.exports import prompt_markdown, prompt_txt
from app.keyboards import (
    ai_models_keyboard,
    categories_keyboard,
    mode_keyboard,
    prompt_actions_keyboard,
    template_items_keyboard,
    templates_keyboard,
)
from app.plans import PREMIUM, get_plan_limits
from app.presentation import prompt_result_chunks
from app.services.openai_service import OpenAIService
from app.templates import TEMPLATE_GROUPS, TEMPLATES


router = Router(name="prompts")
logger = logging.getLogger(__name__)


class PromptFlow(StatesGroup):
    waiting_for_task = State()


async def _show_categories(message: Message, language: str) -> None:
    await message.answer(
        tr(
            language,
            "🧩 Выберите категорию промпта:",
            "🧩 Choose a prompt category:",
        ),
        reply_markup=categories_keyboard(language),
    )


@router.callback_query(F.data == "nav:categories")
async def back_to_categories(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not user.language or not isinstance(callback.message, Message):
        await callback.answer()
        return
    await state.clear()
    await _show_categories(callback.message, user.language)
    await callback.answer()


@router.callback_query(F.data == "nav:templates")
async def back_to_templates(
    callback: CallbackQuery,
    db: Database,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not user.language or not isinstance(callback.message, Message):
        await callback.answer()
        return
    await callback.message.answer(
        tr(user.language, "📚 Шаблоны", "📚 Templates"),
        reply_markup=templates_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tplgroup:"))
async def choose_template_group(
    callback: CallbackQuery,
    db: Database,
) -> None:
    group = (callback.data or "").split(":", 1)[-1]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        group not in TEMPLATE_GROUPS
        or not user
        or not user.language
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid template group", show_alert=True)
        return
    title = TEMPLATE_GROUPS[group][1 if user.language == "en" else 0]
    await callback.message.answer(
        title,
        reply_markup=template_items_keyboard(group, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("template:"))
async def choose_template(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    code = (callback.data or "").split(":", 1)[-1]
    template = TEMPLATES.get(code)
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        template is None
        or not user
        or not user.language
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid template", show_alert=True)
        return
    await state.set_state(PromptFlow.waiting_for_task)
    await state.update_data(
        category=template.category,
        target_ai=template.target_ai,
        expert=user.plan == PREMIUM,
        variants=1,
        template_code=template.code,
        template_structure=template.structure(user.language),
    )
    await callback.message.answer(
        tr(
            user.language,
            f"📚 Шаблон: {template.title(user.language)}\n\n"
            "Опишите вашу задачу и исходные данные.",
            f"📚 Template: {template.title(user.language)}\n\n"
            "Describe your task and provide the source details.",
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def choose_category(callback: CallbackQuery, db: Database) -> None:
    category = (callback.data or "").split(":", 1)[-1]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        category not in CATEGORIES
        or not user
        or not user.language
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid category", show_alert=True)
        return
    await callback.message.answer(
        tr(user.language, "🤖 Выберите AI:", "🤖 Choose an AI:"),
        reply_markup=ai_models_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai:"))
async def choose_ai(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Invalid selection", show_alert=True)
        return
    _, category, target_ai = parts
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        category not in CATEGORIES
        or target_ai not in AI_MODELS
        or not user
        or not user.language
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid selection", show_alert=True)
        return
    if user.is_blocked:
        await callback.answer("Access blocked", show_alert=True)
        return
    if user.plan == PREMIUM:
        await callback.message.answer(
            tr(
                user.language,
                "⚙️ Выберите режим генерации:",
                "⚙️ Choose generation mode:",
            ),
            reply_markup=mode_keyboard(category, target_ai),
        )
    else:
        await state.set_state(PromptFlow.waiting_for_task)
        await state.update_data(
            category=category,
            target_ai=target_ai,
            expert=False,
            variants=1,
        )
        await callback.message.answer(
            tr(
                user.language,
                "✍️ Опишите задачу для будущего промпта.",
                "✍️ Describe the task for your prompt.",
            )
        )
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def choose_mode(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await callback.answer("Invalid mode", show_alert=True)
        return
    _, category, target_ai, mode = parts
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        not user
        or user.plan != PREMIUM
        or category not in CATEGORIES
        or target_ai not in AI_MODELS
        or mode not in {"standard", "expert", "variants"}
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Premium mode required", show_alert=True)
        return
    await state.set_state(PromptFlow.waiting_for_task)
    await state.update_data(
        category=category,
        target_ai=target_ai,
        expert=mode == "expert",
        variants=3 if mode == "variants" else 1,
    )
    await callback.message.answer(
        tr(
            user.language or "ru",
            "✍️ Опишите задачу для будущего промпта.",
            "✍️ Describe the task for your prompt.",
        )
    )
    await callback.answer()


@router.message(PromptFlow.waiting_for_task, F.text)
async def generate_prompt(
    message: Message,
    db: Database,
    openai_service: OpenAIService,
    state: FSMContext,
) -> None:
    if message.from_user is None or not message.text:
        return
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user or not user.language:
        return
    if user.is_blocked:
        await message.answer(
            tr(user.language, "🚫 Ваш аккаунт заблокирован.", "🚫 Account blocked.")
        )
        return
    data = await state.get_data()
    category = data.get("category")
    target_ai = data.get("target_ai")
    if category not in CATEGORIES or target_ai not in AI_MODELS:
        await state.clear()
        await _show_categories(message, user.language)
        return
    if not await db.reserve_request(user):
        await message.answer(
            tr(
                user.language,
                "🔒 Лимит запросов на сегодня исчерпан. /premium",
                "🔒 Daily request limit reached. /premium",
            )
        )
        return
    status = await message.answer(
        tr(user.language, "⏳ Создаю промпт…", "⏳ Crafting your prompt…")
    )
    try:
        task = message.text
        if data.get("template_structure"):
            task = (
                f"{data['template_structure']}\n\n"
                f"User details:\n{message.text}"
            )
        result = await openai_service.generate_prompt(
            task=task,
            category=category,
            target_ai=target_ai,
            language=user.language,
            expert=bool(data.get("expert")),
            variants=int(data.get("variants", 1)),
        )
        prompt_id = await db.save_prompt(
            user.id,
            category,
            target_ai,
            message.text,
            result,
            "expert" if data.get("expert") else "standard",
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
                await message.answer(chunk)
            await message.answer(
                chunks[-1],
                reply_markup=prompt_actions_keyboard(prompt_id, user.language),
            )
        await state.clear()
    except Exception:
        logger.exception("Prompt generation failed for user %s", user.telegram_id)
        await db.release_request(user)
        await status.edit_text(
            tr(
                user.language,
                "Не удалось создать промпт. Попробуйте позже.",
                "Could not create the prompt. Try again later.",
            )
        )


@router.callback_query(F.data.startswith("prompt:"))
async def handle_prompt_action(
    callback: CallbackQuery,
    db: Database,
    openai_service: OpenAIService,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Invalid action", show_alert=True)
        return
    action = parts[1]
    try:
        prompt_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid prompt", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not user.language or not isinstance(callback.message, Message):
        await callback.answer("Prompt unavailable", show_alert=True)
        return
    record = await db.get_prompt(prompt_id, user.id)
    if not record:
        await callback.answer("Prompt unavailable", show_alert=True)
        return
    if action == "copy":
        await callback.message.answer(record.prompt_text)
        await callback.answer(
            tr(user.language, "Текст отправлен", "Prompt sent")
        )
        return
    if action == "favorite":
        first_line = next(
            (line.strip() for line in record.prompt_text.splitlines() if line.strip()),
            "Prompt",
        )
        added = await db.add_favorite(user.id, record.id, first_line)
        await callback.answer(
            tr(
                user.language,
                "Добавлено в избранное" if added else "Уже в избранном",
                "Added to favorites" if added else "Already in favorites",
            ),
            show_alert=True,
        )
        return
    if action in {"export_txt", "export_md"}:
        content = (
            prompt_txt(record)
            if action == "export_txt"
            else prompt_markdown(record)
        )
        extension = "txt" if action == "export_txt" else "md"
        await callback.message.answer_document(
            BufferedInputFile(
                content,
                filename=f"promptcraft-{record.id}.{extension}",
            )
        )
        await callback.answer()
        return
    if action not in {
        "improve", "shorter", "details", "translate_en", "variant"
    }:
        await callback.answer("Invalid action", show_alert=True)
        return
    if action == "improve" and not await db.reserve_improvement(user):
        await callback.answer(
            tr(
                user.language,
                "Лимит улучшений исчерпан",
                "Improvement limit reached",
            ),
            show_alert=True,
        )
        return
    if action != "improve" and not await db.reserve_request(user):
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
        tr(user.language, "✨ Обрабатываю…", "✨ Processing…")
    )
    try:
        if action == "improve":
            result = await openai_service.improve_prompt(
                record.prompt_text,
                record.target_ai,
                user.language,
            )
        else:
            result = await openai_service.transform_prompt(
                action,
                record.prompt_text,
                record.target_ai,
                user.language,
                record.source_text,
            )
        result_language = "en" if action == "translate_en" else user.language
        new_id = await db.save_prompt(
            user.id,
            record.category,
            record.target_ai,
            record.source_text,
            result,
            action,
            result_language,
        )
        chunks = prompt_result_chunks(result, result_language)
        await status.edit_text(
            chunks[0],
            reply_markup=prompt_actions_keyboard(new_id, result_language),
        )
        for chunk in chunks[1:]:
            await callback.message.answer(chunk)
    except Exception:
        logger.exception("Prompt action %s failed", action)
        if action == "improve":
            await db.release_improvement(user)
        else:
            await db.release_request(user)
        await status.edit_text("Error")


@router.callback_query(F.data.startswith("favorite:open:"))
async def open_favorite(callback: CallbackQuery, db: Database) -> None:
    try:
        favorite_id = int((callback.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer("Invalid favorite", show_alert=True)
        return
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not isinstance(callback.message, Message):
        return
    favorite = await db.get_favorite(favorite_id, user.id)
    if not favorite:
        await callback.answer("Favorite unavailable", show_alert=True)
        return
    chunks = prompt_result_chunks(
        favorite.prompt.prompt_text,
        favorite.prompt.language,
    )
    await callback.message.answer(
        chunks[0],
        reply_markup=prompt_actions_keyboard(
            favorite.prompt.id,
            favorite.prompt.language,
        ),
    )
    for chunk in chunks[1:]:
        await callback.message.answer(chunk)
    await callback.answer()


@router.message()
async def fallback(message: Message, db: Database) -> None:
    if message.from_user is None:
        return
    user = await db.get_user_by_telegram_id(message.from_user.id)
    language = user.language if user and user.language else "ru"
    await message.answer(
        tr(
            language,
            "Используйте /new, чтобы создать промпт.",
            "Use /new to create a prompt.",
        )
    )
