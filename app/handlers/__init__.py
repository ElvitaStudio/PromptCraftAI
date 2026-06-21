from aiogram import Router

from app.handlers.admin import router as admin_router
from app.handlers.assistants import router as assistants_router
from app.handlers.broadcast import router as broadcast_router
from app.handlers.claude_chat import router as claude_chat_router
from app.handlers.commands import router as commands_router
from app.handlers.history import router as history_router
from app.handlers.gemini_chat import router as gemini_chat_router
from app.handlers.gpt_chat import router as gpt_chat_router
from app.handlers.language import router as language_router
from app.handlers.news import router as news_router
from app.handlers.payments import router as payments_router
from app.handlers.prompt_chat import router as prompt_chat_router
from app.handlers.prompts import router as prompts_router
from app.handlers.settings import router as settings_router
from app.middlewares import UserProfileMiddleware


def get_router() -> Router:
    router = Router()
    router.message.outer_middleware(UserProfileMiddleware())
    router.include_router(admin_router)
    router.include_router(broadcast_router)
    router.include_router(commands_router)
    router.include_router(news_router)
    router.include_router(language_router)
    router.include_router(payments_router)
    router.include_router(settings_router)
    router.include_router(history_router)
    router.include_router(prompt_chat_router)
    router.include_router(assistants_router)
    router.include_router(gpt_chat_router)
    router.include_router(claude_chat_router)
    router.include_router(gemini_chat_router)
    router.include_router(prompts_router)
    return router
