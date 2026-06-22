from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.assistant_workspace import (
    begin_assistant_search,
    delete_assistant_chat,
    handle_assistant_message,
    handle_assistant_search,
    open_assistant_chat,
    show_assistant_chats,
    start_new_assistant_chat,
)
from app.config import Settings
from app.database import Database
from app.services.gpt_service import GPTService


router = Router(name="gpt_chat")
ASSISTANT = "gpt"


class GPTChatFlow(StatesGroup):
    waiting_for_message = State()
    waiting_for_search = State()


@router.callback_query(F.data == "assistant:gpt:list")
async def gpt_chat_list(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    settings: Settings | None = None,
) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await show_assistant_chats(
            callback.message,
            db,
            callback.from_user.id,
            ASSISTANT,
            settings=settings,
        )
    await callback.answer()


@router.callback_query(F.data == "assistant:gpt:new")
async def gpt_chat_new(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    settings: Settings | None = None,
) -> None:
    await start_new_assistant_chat(
        callback,
        db,
        state,
        ASSISTANT,
        GPTChatFlow.waiting_for_message,
        settings,
    )


@router.callback_query(F.data.startswith("assistant:gpt:open:"))
async def gpt_chat_open(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    settings: Settings | None = None,
) -> None:
    await open_assistant_chat(
        callback,
        db,
        state,
        ASSISTANT,
        int((callback.data or "").rsplit(":", 1)[-1]),
        GPTChatFlow.waiting_for_message,
        settings,
    )


@router.callback_query(F.data.startswith("assistant:gpt:delete:"))
async def gpt_chat_delete(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    settings: Settings | None = None,
) -> None:
    await delete_assistant_chat(
        callback,
        db,
        state,
        ASSISTANT,
        int((callback.data or "").rsplit(":", 1)[-1]),
        settings,
    )


@router.callback_query(F.data == "assistant:gpt:search")
async def gpt_chat_search(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
    settings: Settings | None = None,
) -> None:
    await begin_assistant_search(
        callback,
        db,
        state,
        ASSISTANT,
        GPTChatFlow.waiting_for_search,
        settings,
    )


@router.message(GPTChatFlow.waiting_for_search, F.text)
async def gpt_search_message(
    message: Message,
    db: Database,
    state: FSMContext,
    settings: Settings | None = None,
) -> None:
    await handle_assistant_search(
        message, db, state, ASSISTANT, settings
    )


@router.message(GPTChatFlow.waiting_for_message, F.text)
async def gpt_user_message(
    message: Message,
    db: Database,
    state: FSMContext,
    gpt_service: GPTService,
    settings: Settings | None = None,
) -> None:
    await handle_assistant_message(
        message, db, state, ASSISTANT, gpt_service, settings
    )
