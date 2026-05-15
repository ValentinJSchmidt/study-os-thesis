from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_session
from app.llm.agent import run_agent_turn
from app.models import ChatMessage, ChatSession, User
from app.schemas.chat import MessageIn, MessageOut, SendMessageResponse, SessionOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChatSession:
    chat = ChatSession(user_id=user.id)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ChatSession]:
    rows = await session.scalars(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return list(rows)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ChatMessage]:
    chat = await session.get(ChatSession, session_id)
    if not chat or chat.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    rows = await session.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    )
    return list(rows)


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: int,
    body: MessageIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SendMessageResponse:
    chat = await session.get(ChatSession, session_id)
    if not chat or chat.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if not body.content.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty message")
    new_messages = await run_agent_turn(session, session_id, body.content.strip())
    return SendMessageResponse(messages=[MessageOut.model_validate(m) for m in new_messages])
