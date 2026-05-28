"""Unit tests for ChatService."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.chat.service import ChatService, MAX_TOOL_ITERATIONS
from app.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models import ChatMessage, ChatSession, MessageRole
from app.models.student import Student, StudentCourse
from tests.conftest import _make_orm


@pytest.fixture
def chat_service(
    mock_chat_repo,
    mock_llm_chat,
    mock_llm_embed,
    fake_settings,
    mock_student_repo,
    mock_chair_repo,
    mock_thesis_repo,
) -> ChatService:
    return ChatService(
        chat_repo=mock_chat_repo,
        chat_client=mock_llm_chat,
        embed_client=mock_llm_embed,
        settings=fake_settings,
        student_repo=mock_student_repo,
        chair_repo=mock_chair_repo,
        thesis_repo=mock_thesis_repo,
    )


def _make_session(session_id: int = 1, user_id: int = 1) -> ChatSession:
    return _make_orm(ChatSession, id=session_id, user_id=user_id)


def _make_message(
    msg_id: int = 1,
    session_id: int = 1,
    role: MessageRole = MessageRole.user,
    content: str = "hello",
    tool_calls=None,
    tool_name=None,
) -> ChatMessage:
    return _make_orm(
        ChatMessage,
        id=msg_id,
        session_id=session_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_name=tool_name,
    )


def _llm_response(content: str, tool_calls=None) -> dict:
    msg = {"role": "assistant", "content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return {"message": msg}


def _tool_call(name: str, arguments: dict) -> dict:
    return {"function": {"name": name, "arguments": arguments}}


@pytest.mark.unit
class TestCreateSession:
    async def test_delegates_to_repo(self, chat_service, mock_chat_repo):
        expected = _make_session()
        mock_chat_repo.create_session.return_value = expected

        result = await chat_service.create_session(1)

        mock_chat_repo.create_session.assert_called_once_with(1)
        assert result.id == expected.id


@pytest.mark.unit
class TestListSessions:
    async def test_delegates_to_repo(self, chat_service, mock_chat_repo):
        mock_chat_repo.list_sessions.return_value = []

        await chat_service.list_sessions(1)

        mock_chat_repo.list_sessions.assert_called_once_with(1)


@pytest.mark.unit
class TestGetMessages:
    async def test_validates_ownership(self, chat_service, mock_chat_repo):
        session = _make_session(session_id=1, user_id=99)
        mock_chat_repo.get_session.return_value = session

        with pytest.raises(ForbiddenException):
            await chat_service.get_messages(session_id=1, user_id=1)

    async def test_session_not_found(self, chat_service, mock_chat_repo):
        mock_chat_repo.get_session.return_value = None

        with pytest.raises(NotFoundException):
            await chat_service.get_messages(session_id=999, user_id=1)


@pytest.mark.unit
class TestSendMessage:
    @pytest.fixture(autouse=True)
    def _setup(self, mock_chat_repo, mock_student_repo):
        mock_chat_repo.get_session.return_value = _make_session()
        mock_chat_repo.list_messages.return_value = []
        mock_chat_repo.create_message.return_value = _make_message()
        mock_chat_repo.refresh.return_value = None
        mock_student_repo.get_by_user_id.return_value = None

    async def test_persists_user_message(self, chat_service, mock_chat_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_response("Hi there!")

        await chat_service.send_message(session_id=1, user_id=1, content="Hello")

        calls = mock_chat_repo.create_message.call_args_list
        first_call = calls[0]
        assert first_call.kwargs["role"] == MessageRole.user
        assert first_call.kwargs["content"] == "Hello"

    async def test_no_tool_calls(self, chat_service, mock_chat_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_response("Simple answer.")

        await chat_service.send_message(session_id=1, user_id=1, content="Question")

        mock_llm_chat.chat.assert_called_once()
        mock_chat_repo.commit.assert_called_once()

    async def test_with_tool_call(self, chat_service, mock_chat_repo, mock_llm_chat, monkeypatch):
        mock_llm_chat.chat.side_effect = [
            _llm_response(
                "Let me search.",
                tool_calls=[_tool_call("search_theses", {"query": "ML"})],
            ),
            _llm_response("Here are the results."),
        ]

        monkeypatch.setattr(
            "app.chat.service.search_theses_with_client",
            AsyncMock(return_value=[{"id": 1, "title": "Thesis"}]),
        )

        await chat_service.send_message(session_id=1, user_id=1, content="Find ML theses")

        assert mock_llm_chat.chat.call_count == 2

    async def test_max_iterations(self, chat_service, mock_chat_repo, mock_llm_chat, monkeypatch):
        mock_llm_chat.chat.return_value = _llm_response(
            "Searching...",
            tool_calls=[_tool_call("search_theses", {"query": "test"})],
        )

        monkeypatch.setattr(
            "app.chat.service.search_theses_with_client",
            AsyncMock(return_value=[]),
        )

        await chat_service.send_message(session_id=1, user_id=1, content="Loop forever")

        assert mock_llm_chat.chat.call_count == MAX_TOOL_ITERATIONS
        last_create = mock_chat_repo.create_message.call_args_list[-1]
        assert "stopped" in last_create.kwargs.get("content", "").lower() or "limit" in last_create.kwargs.get("content", "").lower()

    async def test_empty_message_raises(self, chat_service):
        with pytest.raises(BadRequestException, match="Empty message"):
            await chat_service.send_message(session_id=1, user_id=1, content="  ")

    async def test_session_not_found(self, chat_service, mock_chat_repo):
        mock_chat_repo.get_session.return_value = None

        with pytest.raises(NotFoundException):
            await chat_service.send_message(session_id=999, user_id=1, content="Hello")

    async def test_wrong_user_raises(self, chat_service, mock_chat_repo):
        mock_chat_repo.get_session.return_value = _make_session(user_id=99)

        with pytest.raises(ForbiddenException):
            await chat_service.send_message(session_id=1, user_id=1, content="Hello")


@pytest.mark.unit
class TestBuildStudentContext:
    async def test_with_courses(self, chat_service, mock_student_repo):
        course = _make_orm(StudentCourse, course_name="Machine Learning", credits=5.0, grade="1,3")
        student = _make_orm(Student, user_id=1, gpa=1.3, program="CS", semester=4, courses=[course])
        mock_student_repo.get_by_user_id.return_value = student

        result = await chat_service._build_student_context(1)

        assert result is not None
        assert "1.3" in result
        assert "Machine Learning" in result

    async def test_no_student(self, chat_service, mock_student_repo):
        mock_student_repo.get_by_user_id.return_value = None

        result = await chat_service._build_student_context(1)

        assert result is None


@pytest.mark.unit
class TestToolSearchChairs:
    async def test_calls_embed_and_repo(self, chat_service, mock_llm_embed, mock_chair_repo):
        mock_chair_repo.search_by_embedding.return_value = [{"id": 1, "name": "Chair"}]

        result = await chat_service._tool_search_chairs({"query": "robotics", "k": 3})

        mock_llm_embed.embed.assert_called_once()
        mock_chair_repo.search_by_embedding.assert_called_once()
        data = json.loads(result)
        assert "results" in data

    async def test_embed_failure_returns_error(self, chat_service, mock_llm_embed):
        mock_llm_embed.embed.side_effect = Exception("LLM down")

        result = await chat_service._tool_search_chairs({"query": "robotics"})

        data = json.loads(result)
        assert "error" in data


@pytest.mark.unit
class TestToolUnknown:
    async def test_unknown_tool_returns_error(self, chat_service):
        result = await chat_service._execute_tool_call("nonexistent_tool", {}, user_id=1, chat_session_id=1)

        data = json.loads(result)
        assert "error" in data
        assert "unknown tool" in data["error"]
