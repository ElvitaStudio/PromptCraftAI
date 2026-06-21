from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.config import load_settings
from app.database import Database
from app.handlers import get_router
from app.services.openai_service import OpenAIService


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="new", description="New prompt"),
            BotCommand(command="history", description="Prompt history"),
            BotCommand(command="templates", description="Templates"),
            BotCommand(command="favorites", description="Favorites"),
            BotCommand(command="daily", description="Prompt of the Day"),
            BotCommand(command="limits", description="My limits"),
            BotCommand(command="premium", description="Plans"),
            BotCommand(command="invite", description="Invite a friend"),
            BotCommand(command="language", description="Language"),
            BotCommand(command="help", description="Help"),
            BotCommand(command="paysupport", description="Payment support"),
        ]
    )


async def run_bot() -> None:
    settings = load_settings()
    db = Database(settings.database_path)
    await db.initialize()
    bot = Bot(settings.telegram_bot_token)
    info = await bot.me()
    if not info.username:
        await bot.session.close()
        raise RuntimeError("Bot username is not configured")
    dispatcher = Dispatcher()
    dispatcher.include_router(get_router())
    service = OpenAIService(
        settings.openai_api_key,
        settings.generation_model,
    )
    try:
        await set_commands(bot)
        await dispatcher.start_polling(
            bot,
            db=db,
            settings=settings,
            openai_service=service,
            bot_username=info.username,
        )
    finally:
        await bot.session.close()
