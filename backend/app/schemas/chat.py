from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import MessageRole


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: MessageRole
    content: str
    tool_calls: dict | list | None = None
    tool_name: str | None = None
    created_at: datetime


class SendMessageResponse(BaseModel):
    """All messages produced by this turn (user + any tool + final assistant)."""

    messages: list[MessageOut]
