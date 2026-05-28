"""Tests for the chat agent loop Celery task."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chat.tasks import _process_chat_turn_work, process_chat_turn


def _acm(session):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.mark.unit
class TestProcessChatTurnWiring:
    def test_uses_chat_event_names(self):
        with patch("app.chat.tasks.execute_task") as ex:
            process_chat_turn(session_id=2, user_id=1, content="Hi", job_id="j")

        kw = ex.call_args.kwargs
        assert kw["success_event"] == "chat_turn_completed"
        assert kw["started_event"] == "chat_turn_started"
        assert kw["started_data"] == {"session_id": 2}


@pytest.mark.unit
class TestProcessChatTurnWork:
    async def test_runs_agent_and_counts_messages(self):
        session = AsyncMock()
        svc = AsyncMock()
        svc.send_message.return_value = ["m1", "m2", "m3"]
        settings = SimpleNamespace(ollama_embed_model="m")

        with patch("app.db.SessionLocal", return_value=_acm(session)), \
             patch("app.chat.repository.ChatRepository", return_value=AsyncMock()), \
             patch("app.students.repository.StudentRepository", return_value=AsyncMock()), \
             patch("app.chairs.repository.ChairRepository", return_value=AsyncMock()), \
             patch("app.theses.repository.ThesisRepository", return_value=AsyncMock()), \
             patch("app.chat.service.ChatService", return_value=svc), \
             patch("app.llm.factory.build_chat_client", return_value=AsyncMock()), \
             patch("app.llm.factory.build_embed_client", return_value=AsyncMock()):
            result = await _process_chat_turn_work(2, 1, "Hello", settings)

        svc.send_message.assert_awaited_once_with(2, 1, "Hello")
        assert result == {"session_id": 2, "message_count": 3}
