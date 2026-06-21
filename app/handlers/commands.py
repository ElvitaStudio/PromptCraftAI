from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from app.catalog import tr
from app.database import Database
from app.history import history_chunks
from app.keyboards import (
    categories_keyboard,
    favorites_keyboard,
    language_keyboard,
    premium_keyboard,
    templates_keyboard,
)
from app.middlewares import telegram_profile
from app.plans import PREMIUM, get_plan_limits
from app.referrals import (
    REFERRAL_REWARD_DAYS,
    build_referral_link,
    invite_message,
    parse_referral_payload,
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
    if not result.user.language:
        await message.answer(
            "🌐 Выберите язык / Choose your language",
            reply_markup=language_keyboard(),
        )
        return
    await message.answer(
        tr(
            result.user.language,
            "🚀 Добро пожаловать в PromptCraft AI!\n\nВыберите категорию:",
            "🚀 Welcome to PromptCraft AI!\n\nChoose a category:",
        ),
        reply_markup=categories_keyboard(result.user.language),
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
        tr(user.language, "🧩 Выберите категорию:", "🧩 Choose a category:"),
        reply_markup=categories_keyboard(user.language),
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
            "/language — язык",
            "Commands:\n/new — new prompt\n/history — history\n"
            "/limits — limits\n/premium — plans\n/invite — referrals\n"
            "/templates — templates\n/favorites — favorites\n"
            "/language — language",
        )
    )


@router.message(Command("history"))
async def history_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    for chunk in history_chunks(
        await db.get_prompt_history(user),
        user.language or "ru",
    ):
        await message.answer(chunk)


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
    await message.answer(
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


@router.message(Command("premium"))
async def premium_command(message: Message, db: Database) -> None:
    user = await db.get_user_by_telegram_id(message.from_user.id)
    language = user.language if user and user.language else "ru"
    text = tr(
        language,
        "🆓 Free\n• 5 запросов в день\n• История 5\n"
        "• 1 улучшение промпта\n\n"
        "⭐ Pro — 199 Stars\n• 100 запросов в день\n• История 30\n\n"
        "👑 Premium — 399 Stars\n• Безлимитные запросы\n"
        "• Expert mode\n• 3 варианта ответа",
        "🆓 Free\n• 5 requests/day\n• History 5\n"
        "• 1 prompt improvement\n\n"
        "⭐ Pro — 199 Stars\n• 100 requests/day\n• History 30\n\n"
        "👑 Premium — 399 Stars\n• Unlimited requests\n"
        "• Expert mode\n• 3 response variants",
    )
    await message.answer(text, reply_markup=premium_keyboard())


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
