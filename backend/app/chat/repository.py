from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage, ChatSession, MessageRole


class ChatRepository:
    """Data-access layer for `chat_sessions` and `chat_messages` tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- Sessions ----

    async def create_session(self, user_id: int) -> ChatSession:
        chat = ChatSession(user_id=user_id)
        self._session.add(chat)
        await self._session.flush()
        await self._session.refresh(chat)
        await self._session.commit()
        return chat

    async def list_sessions(self, user_id: int) -> list[ChatSession]:
        rows = await self._session.scalars(select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()))
        return list(rows)

    async def get_session(self, session_id: int) -> ChatSession | None:
        return await self._session.get(ChatSession, session_id)

    # ---- Messages ----

    async def list_messages(self, session_id: int) -> list[ChatMessage]:
        rows = await self._session.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc()))
        return list(rows)

    async def create_message(
        self,
        session_id: int,
        role: MessageRole,
        content: str,
        tool_calls: Any | None = None,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
        *,
        flush_only: bool = False,
    ) -> ChatMessage:
        """Create and persist a chat message.

        If ``flush_only`` is True the message is flushed (ID assigned) but not
        committed — the caller is expected to commit the transaction later.
        This is useful inside the agent loop where multiple messages are created
        within a single logical turn.
        """
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
        )
        self._session.add(msg)
        if flush_only:
            await self._session.flush()
        else:
            await self._session.commit()
            await self._session.refresh(msg)
        return msg

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, instance: object) -> None:
        await self._session.refresh(instance)
