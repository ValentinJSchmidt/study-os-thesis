from fastapi import APIRouter, status

from app.dependencies import ChatServiceDep, CurrentUserDep
from app.models import ChatMessage, ChatSession
from app.schemas.chat import MessageIn, MessageOut, SendMessageResponse, SessionOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> ChatSession:
    return await chat_service.create_session(user.id)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> list[ChatSession]:
    return await chat_service.list_sessions(user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: int,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> list[ChatMessage]:
    return await chat_service.get_messages(session_id, user.id)


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: int,
    body: MessageIn,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> SendMessageResponse:
    new_messages = await chat_service.send_message(session_id, user.id, body.content)
    return SendMessageResponse(messages=[MessageOut.model_validate(m) for m in new_messages])
