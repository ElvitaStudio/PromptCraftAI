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
from app.database import Database
from app.services.claude_service import ClaudeService


router = Router(name="claude_chat")
ASSISTANT = "claude"


class ClaudeChatFlow(StatesGroup):
    waiting_for_message = State()
    waiting_for_search = State()


@router.callback_query(F.data == "assistant:claude:list")
async def claude_chat_list(
    callback: CallbackQuery, db: Database, state: FSMContext
) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await show_assistant_chats(
            callback.message, db, callback.from_user.id, ASSISTANT
        )
    await callback.answer()


@router.callback_query(F.data == "assistant:claude:new")
async def claude_chat_new(
    callback: CallbackQuery, db: Database, state: FSMContext
) -> None:
    await start_new_assistant_chat(
        callback, db, state, ASSISTANT, ClaudeChatFlow.waiting_for_message
    )


@router.callback_query(F.data.startswith("assistant:claude:open:"))
async def claude_chat_open(
    callback: CallbackQuery, db: Database, state: FSMContext
) -> None:
    await open_assistant_chat(
        callback,
        db,
        state,
        ASSISTANT,
        int((callback.data or "").rsplit(":", 1)[-1]),
        ClaudeChatFlow.waiting_for_message,
    )


@router.callback_query(F.data.startswith("assistant:claude:delete:"))
async def claude_chat_delete(
    callback: CallbackQuery, db: Database, state: FSMContext
) -> None:
    await delete_assistant_chat(
        callback,
        db,
        state,
        ASSISTANT,
        int((callback.data or "").rsplit(":", 1)[-1]),
    )


@router.callback_query(F.data == "assistant:claude:search")
async def claude_chat_search(
    callback: CallbackQuery, db: Database, state: FSMContext
) -> None:
    await begin_assistant_search(
        callback, db, state, ASSISTANT, ClaudeChatFlow.waiting_for_search
    )


@router.message(ClaudeChatFlow.waiting_for_search, F.text)
async def claude_search_message(
    message: Message, db: Database, state: FSMContext
) -> None:
    await handle_assistant_search(message, db, state, ASSISTANT)


@router.message(ClaudeChatFlow.waiting_for_message, F.text)
async def claude_user_message(
    message: Message,
    db: Database,
    state: FSMContext,
    claude_service: ClaudeService,
) -> None:
    await handle_assistant_message(
        message, db, state, ASSISTANT, claude_service
    )
