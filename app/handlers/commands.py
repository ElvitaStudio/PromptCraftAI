from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message

from app.catalog import tr
from app.daily_prompts import prompt_of_the_day
from app.database import Database, RegistrationResult
from app.handlers.history import show_history_page
from app.keyboards import (
    favorites_keyboard,
    language_keyboard,
    premium_keyboard,
    prompt_actions_keyboard,
    templates_keyboard,
    workflow_keyboard,
)
from app.middlewares import telegram_profile
from app.plans import PREMIUM, get_plan_limits
from app.presentation import prompt_result_chunks
from app.referrals import (
    REFERRAL_REWARD_DAYS,
    build_referral_link,
    invite_message,
    parse_referral_payload,
)
from app.subscriptions import premium_text
from app.trial import (
    existing_user_trial_message,
    infer_telegram_language,
    new_user_trial_message,
    trial_status_text,
)


router = Router(name="commands")


@router.message(CommandStart())
async def start_command(
    message: Message,
    command: CommandObject,
    db: Database,
) -> None:
    profile = telegram_profile(message)
    result = await db.register_user(
        telegram_id=profile[0],
        username=profile[1],
        first_name=profile[2],
        last_name=profile[3],
        full_name=profile[4],
        referred_by_telegram_id=parse_referral_payload(command.args),
        reward_days=REFERRAL_REWARD_DAYS,
    )
    activate = getattr(db, "activate_trial_once", None)
    activation = (
        await activate(profile[0])
        if activate is not None
        else None
    )
    trial_language = (
        result.user.language
        or infer_telegram_language(message.from_user)
    )
    if (
        activation is not None
        and activation.notification_required
    ):
        await message.answer(
            (
                new_user_trial_message(trial_language)
                if result.created
                else existing_user_trial_message(trial_language)
            )
        )
        result = RegistrationResult(
            activation.user,
            result.created,
            result.referral_rewarded,
        )
    if not result.user.language:
        await message.answer(
            "🌐 Выберите язык / Choose your language",
            reply_markup=language_keyboard(),
        )
        return
    await message.answer(
        tr(
            result.user.language,
            "🚀 Добро пожаловать в PromptCraft AI!\n\nЧто вы хотите сделать?",
            "🚀 Welcome to PromptCraft AI!\n\nWhat would you like to do?",
        ),
        reply_markup=workflow_keyboard(
            result.user.language,
            has_saved_settings=True,
        ),
    )


@router.message(Command("new"))
async def new_prompt(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user or not user.language:
        await message.answer(
            "🌐 Выберите язык / Choose your language",
            reply_markup=language_keyboard(),
        )
        return
    await message.answer(
        tr(
            user.language,
            "🚀 Что вы хотите сделать?",
            "🚀 What would you like to do?",
        ),
        reply_markup=workflow_keyboard(
            user.language,
            has_saved_settings=True,
        ),
    )


@router.message(Command("language"))
async def language_command(message: Message) -> None:
    await message.answer(
        "🌐 Выберите язык / Choose your language",
        reply_markup=language_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    language = user.language if user and user.language else "ru"
    await message.answer(
        tr(
            language,
            "Команды:\n/new — новый промпт\n/history — история\n"
            "/limits — лимиты\n/premium — тарифы\n/invite — рефералы\n"
            "/templates — шаблоны\n/favorites — избранное\n"
            "/daily — промпт дня\n"
            "/chat — Prompt Chat\n/settings — настройки\n"
            "/language — язык",
            "Commands:\n/new — new prompt\n/history — history\n"
            "/limits — limits\n/premium — plans\n/invite — referrals\n"
            "/templates — templates\n/favorites — favorites\n"
            "/daily — prompt of the day\n"
            "/chat — Prompt Chat\n/settings — settings\n"
            "/language — language",
        )
    )


@router.message(Command("history"))
async def history_command(message: Message, db: Database) -> None:
    if message.from_user:
        await show_history_page(message, db, message.from_user.id)


@router.message(Command("limits"))
async def limits_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    requests = await db.get_request_usage(user)
    improvements = await db.get_improvement_usage(user)
    limits = get_plan_limits(user.plan)
    unlimited = "∞"
    language = user.language or "ru"
    text = (
        tr(
            language,
            f"📊 Тариф: {limits.name}\n\n"
            f"🧩 Запросы: {requests.used}/{requests.limit or unlimited}\n"
            f"✨ Улучшения: {improvements.used}/"
            f"{improvements.limit or unlimited}\n"
            f"📜 История: {limits.history_limit}",
            f"📊 Plan: {limits.name}\n\n"
            f"🧩 Requests: {requests.used}/{requests.limit or unlimited}\n"
            f"✨ Improvements: {improvements.used}/"
            f"{improvements.limit or unlimited}\n"
            f"📜 History: {limits.history_limit}",
        )
    )
    trial = trial_status_text(user, language)
    if trial:
        text = f"{trial}\n\n━━━━━━━━━━━━\n\n{text}"
    await message.answer(text)


@router.message(Command("premium"))
async def premium_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    language = user.language if user and user.language else "ru"
    await message.answer(
        premium_text(language),
        reply_markup=premium_keyboard(language),
    )


@router.callback_query(F.data == "nav:premium")
async def premium_callback(callback: CallbackQuery, db: Database) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user and user.language else "ru"
    if isinstance(callback.message, Message):
        await callback.message.answer(
            premium_text(language),
            reply_markup=premium_keyboard(language),
        )
    await callback.answer()


@router.message(Command("invite"))
async def invite_command(
    message: Message,
    db: Database,
    bot_username: str,
) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    await message.answer(
        invite_message(
            build_referral_link(bot_username, user.telegram_id),
            user.language or "ru",
        )
    )


@router.message(Command("templates"))
async def templates_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    language = user.language if user and user.language else "ru"
    await message.answer(
        tr(language, "📚 Шаблоны", "📚 Templates"),
        reply_markup=templates_keyboard(language),
    )


@router.message(Command("favorites"))
async def favorites_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    language = user.language or "ru"
    favorites = await db.get_favorites(user.id)
    if not favorites:
        await message.answer(
            tr(
                language,
                "⭐ Избранное пока пусто.",
                "⭐ Favorites are empty.",
            )
        )
        return
    await message.answer(
        tr(language, "⭐ Избранное", "⭐ Favorites"),
        reply_markup=favorites_keyboard(
            [(item.id, item.title) for item in favorites],
            language,
        ),
    )


@router.message(Command("daily"))
async def daily_prompt_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    language = user.language or "ru"
    prompt = prompt_of_the_day(language)
    prompt_id = await db.save_prompt(
        user.id,
        "text",
        "chatgpt",
        "Prompt of the Day",
        prompt,
        "daily",
        language,
    )
    chunks = prompt_result_chunks(prompt, language)
    for index, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            reply_markup=(
                prompt_actions_keyboard(prompt_id, language)
                if index == len(chunks) - 1
                else None
            ),
        )
