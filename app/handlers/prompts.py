from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.catalog import AI_MODELS, CATEGORIES, tr
from app.daily_prompts import prompt_of_the_day
from app.database import Database
from app.exports import prompt_markdown, prompt_txt
from app.keyboards import (
    ai_models_keyboard,
    categories_keyboard,
    favorites_keyboard,
    mode_keyboard,
    programmer_modes_keyboard,
    prompt_actions_keyboard,
    response_style_keyboard,
    template_items_keyboard,
    templates_keyboard,
    workflow_keyboard,
)
from app.plans import PREMIUM, get_plan_limits
from app.programmer_templates import PROGRAMMER_TEMPLATES
from app.presentation import prompt_result_chunks
from app.prompt_profiles import (
    CODING_ASSISTANTS,
    DIFFICULTIES,
    RESPONSE_STYLES,
    profile_summary,
)
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


async def _save_preferences(
    db: Database,
    telegram_id: int,
    **values: str,
) -> None:
    updater = getattr(db, "update_user_preferences", None)
    if updater is not None:
        await updater(telegram_id, **values)


async def _show_workflows(message: Message, user) -> None:
    await message.answer(
        tr(
            user.language or "ru",
            "🚀 Что вы хотите сделать?",
            "🚀 What would you like to do?",
        ),
        reply_markup=workflow_keyboard(
            user.language or "ru",
            has_saved_settings=True,
        ),
    )


def _task_message(language: str, workflow: str) -> str:
    return tr(
        language,
        (
            "🔧 Пришлите ваш текущий промпт. Я превращу его в сильный "
            "профессиональный промпт."
            if workflow == "optimize"
            else "✍️ Опишите задачу для будущего промпта."
        ),
        (
            "🔧 Send your current prompt. I will transform it into a strong "
            "professional prompt."
            if workflow == "optimize"
            else "✍️ Describe the task for your prompt."
        ),
    )


async def _prepare_from_preferences(
    message: Message,
    user,
    state: FSMContext,
) -> None:
    difficulty = user.last_difficulty
    if difficulty == "expert" and user.plan != PREMIUM:
        difficulty = "advanced"
    await state.set_state(PromptFlow.waiting_for_task)
    await state.update_data(
        category=user.last_category,
        target_ai=user.last_target_ai,
        difficulty=difficulty,
        response_style=user.last_response_style,
        workflow=user.last_workflow,
        expert=difficulty == "expert",
        variants=1,
    )
    await message.answer(
        tr(
            user.language or "ru",
            "⚡ Использую последние настройки:\n\n",
            "⚡ Using your last settings:\n\n",
        )
        + profile_summary(
            user.language or "ru",
            user.last_category,
            user.last_target_ai,
            difficulty,
            user.last_response_style,
        )
        + "\n\n"
        + _task_message(user.language or "ru", user.last_workflow)
    )


@router.callback_query(F.data.startswith("workflow:"))
async def choose_workflow(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    workflow = (callback.data or "").split(":", 1)[-1]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        workflow not in {"create", "optimize"}
        or not user
        or not user.language
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid mode", show_alert=True)
        return
    await state.clear()
    await state.update_data(workflow=workflow)
    await _save_preferences(
        db,
        user.telegram_id,
        workflow=workflow,
    )
    await callback.message.answer(
        tr(
            user.language,
            "🧩 Выберите категорию:",
            "🧩 Choose a category:",
        ),
        reply_markup=categories_keyboard(
            user.language,
            selected=user.last_category,
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:last")
async def use_last_settings(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not user.language or not isinstance(callback.message, Message):
        await callback.answer()
        return
    await _prepare_from_preferences(callback.message, user, state)
    await callback.answer()


@router.callback_query(F.data == "nav:daily")
async def show_prompt_of_the_day(
    callback: CallbackQuery,
    db: Database,
) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not user.language or not isinstance(callback.message, Message):
        await callback.answer()
        return
    prompt = prompt_of_the_day(user.language)
    prompt_id = await db.save_prompt(
        user.id,
        "text",
        "chatgpt",
        "Prompt of the Day",
        prompt,
        "daily",
        user.language,
    )
    chunks = prompt_result_chunks(prompt, user.language)
    for index, chunk in enumerate(chunks):
        await callback.message.answer(
            chunk,
            reply_markup=(
                prompt_actions_keyboard(prompt_id, user.language)
                if index == len(chunks) - 1
                else None
            ),
        )
    await callback.answer()


@router.callback_query(F.data == "nav:favorites")
async def show_favorites(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user or not user.language or not isinstance(callback.message, Message):
        await callback.answer()
        return
    favorites = await db.get_favorites(user.id)
    if not favorites:
        await callback.answer(
            tr(user.language, "Избранное пока пусто", "Favorites are empty"),
            show_alert=True,
        )
        return
    await callback.message.answer(
        tr(user.language, "⭐ Избранное", "⭐ Favorites"),
        reply_markup=favorites_keyboard(
            [(item.id, item.title) for item in favorites],
            user.language,
        ),
    )
    await callback.answer()


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
        difficulty="expert" if user.plan == PREMIUM else "advanced",
        response_style="professional",
        workflow="create",
        expert=user.plan == PREMIUM,
        variants=1,
        template_code=template.code,
        template_structure=template.structure(user.language),
    )
    await _save_preferences(
        db,
        user.telegram_id,
        category=template.category,
        target_ai=template.target_ai,
        difficulty="expert" if user.plan == PREMIUM else "advanced",
        response_style="professional",
        workflow="create",
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
    await _save_preferences(
        db,
        user.telegram_id,
        category=category,
    )
    await callback.message.answer(
        tr(user.language, "🤖 Выберите AI:", "🤖 Choose an AI:"),
        reply_markup=ai_models_keyboard(category, selected=user.last_target_ai),
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
    difficulty = user.last_difficulty
    if difficulty == "expert" and user.plan != PREMIUM:
        difficulty = "advanced"
    await state.set_state(PromptFlow.waiting_for_task)
    await state.update_data(
        category=category,
        target_ai=target_ai,
        difficulty=difficulty,
        response_style=user.last_response_style,
        workflow=user.last_workflow,
        expert=difficulty == "expert",
        variants=1,
    )
    await _save_preferences(
        db,
        user.telegram_id,
        category=category,
        target_ai=target_ai,
    )
    if category == "code" or target_ai in CODING_ASSISTANTS:
        await callback.message.answer(
            tr(
                user.language,
                "🧰 Выберите режим для разработчика:",
                "🧰 Choose a developer mode:",
            ),
            reply_markup=programmer_modes_keyboard(user.language),
        )
    await callback.message.answer(
        tr(
            user.language,
            "⚙️ Выберите уровень сложности:",
            "⚙️ Choose a difficulty level:",
        ),
        reply_markup=mode_keyboard(category, target_ai, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("devmode:"))
async def choose_programmer_mode(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    code = (callback.data or "").split(":", 1)[-1]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    if (
        (code != "skip" and code not in PROGRAMMER_TEMPLATES)
        or not user
        or not user.language
        or (
            data.get("category") != "code"
            and data.get("target_ai") not in CODING_ASSISTANTS
        )
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid developer mode", show_alert=True)
        return
    if code != "skip":
        template = PROGRAMMER_TEMPLATES[code]
        await state.update_data(
            programmer_mode=code,
            template_structure=template.structure(user.language),
        )
    await callback.message.answer(
        tr(
            user.language,
            "⚙️ Теперь выберите уровень сложности:",
            "⚙️ Now choose a difficulty level:",
        ),
        reply_markup=mode_keyboard(
            data["category"],
            data["target_ai"],
            user.language,
        ),
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
    normalized_mode = "simple" if mode == "standard" else mode
    if (
        not user
        or category not in CATEGORIES
        or target_ai not in AI_MODELS
        or normalized_mode not in {
            "simple", "advanced", "expert", "variants"
        }
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid mode", show_alert=True)
        return
    if normalized_mode in {"expert", "variants"} and user.plan != PREMIUM:
        await callback.answer(
            tr(
                user.language or "ru",
                "👑 Expert доступен только в Premium. Подробнее: /premium",
                "👑 Expert is available only with Premium. See /premium",
            ),
            show_alert=True,
        )
        return
    difficulty = (
        "expert" if normalized_mode == "variants" else normalized_mode
    )
    await state.update_data(
        category=category,
        target_ai=target_ai,
        difficulty=difficulty,
        expert=difficulty == "expert",
        variants=3 if normalized_mode == "variants" else 1,
    )
    await _save_preferences(
        db,
        user.telegram_id,
        category=category,
        target_ai=target_ai,
        difficulty=difficulty,
    )
    await callback.message.answer(
        tr(
            user.language or "ru",
            "🎨 Выберите стиль ответа:",
            "🎨 Choose a response style:",
        ),
        reply_markup=response_style_keyboard(
            category,
            target_ai,
            user.language or "ru",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("style:"))
async def choose_response_style(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await callback.answer("Invalid style", show_alert=True)
        return
    _, category, target_ai, response_style = parts
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if (
        not user
        or not user.language
        or category not in CATEGORIES
        or target_ai not in AI_MODELS
        or response_style not in RESPONSE_STYLES
        or not isinstance(callback.message, Message)
    ):
        await callback.answer("Invalid style", show_alert=True)
        return
    await state.set_state(PromptFlow.waiting_for_task)
    await state.update_data(response_style=response_style)
    await _save_preferences(
        db,
        user.telegram_id,
        category=category,
        target_ai=target_ai,
        response_style=response_style,
    )
    data = await state.get_data()
    await callback.message.answer(
        _task_message(user.language, data.get("workflow", "create"))
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
        difficulty = data.get("difficulty", "simple")
        response_style = data.get("response_style", "professional")
        workflow = data.get("workflow", "create")
        if workflow == "optimize":
            result = await openai_service.optimize_prompt(
                prompt=task,
                category=category,
                target_ai=target_ai,
                language=user.language,
                difficulty=difficulty,
                response_style=response_style,
                variants=int(data.get("variants", 1)),
            )
        else:
            result = await openai_service.generate_prompt(
                task=task,
                category=category,
                target_ai=target_ai,
                language=user.language,
                expert=difficulty == "expert",
                variants=int(data.get("variants", 1)),
                difficulty=difficulty,
                response_style=response_style,
                workflow="create",
            )
        prompt_id = await db.save_prompt(
            user.id,
            category,
            target_ai,
            message.text,
            result,
            f"{workflow}:{difficulty}:{response_style}",
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
