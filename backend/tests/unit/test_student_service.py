"""Unit tests for StudentService."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.exceptions import BadRequestException, NotFoundException
from app.models.student import Student
from app.students.service import StudentService
from tests.conftest import _make_orm


@pytest.fixture
def student_service(mock_student_repo, mock_llm_chat, mock_llm_embed, fake_settings) -> StudentService:
    return StudentService(mock_student_repo, mock_llm_chat, mock_llm_embed, fake_settings)


def _make_student(**overrides) -> Student:
    defaults = dict(user_id=1, gpa=1.7, program="CS", semester=4, profile_embedding=None, courses=[])
    return _make_orm(Student, **{**defaults, **overrides})


def _llm_json_response(data: dict) -> dict:
    return {
        "message": {
            "role": "assistant",
            "content": json.dumps(data),
        }
    }


@pytest.mark.unit
class TestGetProfile:
    async def test_returns_student(self, student_service, mock_student_repo):
        expected = _make_student()
        mock_student_repo.get_by_user_id.return_value = expected

        result = await student_service.get_profile(1)

        assert result.user_id == 1
        mock_student_repo.get_by_user_id.assert_called_once_with(1)

    async def test_not_found_raises(self, student_service, mock_student_repo):
        mock_student_repo.get_by_user_id.return_value = None

        with pytest.raises(NotFoundException):
            await student_service.get_profile(999)


@pytest.mark.unit
class TestUploadTranscript:
    @pytest.fixture(autouse=True)
    def _patch_pdf(self, monkeypatch):
        self._extract_mock = AsyncMock(return_value="Page 1 text\n\n---\n\nPage 2 text")
        monkeypatch.setattr("app.students.service._extract_pdf_text", self._extract_mock)

    async def test_calls_extract_pdf(self, student_service, mock_student_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": 1.7,
                "courses": [{"course_name": "ML", "credits": 5.0, "grade": "1,3", "semester_taken": "WS 2024"}],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"fake-pdf-bytes")

        self._extract_mock.assert_called_once_with(b"fake-pdf-bytes")

    async def test_calls_llm_chat_with_json_format(self, student_service, mock_student_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": 2.0,
                "courses": [{"course_name": "DB", "credits": 6.0, "grade": "2,0"}],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"pdf-bytes")

        mock_llm_chat.chat.assert_called_once()
        call_kwargs = mock_llm_chat.chat.call_args
        assert call_kwargs.kwargs.get("format") == "json"

    async def test_parses_llm_json_response(self, student_service, mock_student_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": 1.5,
                "courses": [
                    {"course_name": "ML", "credits": 5.0, "grade": "1,3", "semester_taken": "WS 2024"},
                    {"course_name": "DB", "credits": 6.0, "grade": "2,0", "semester_taken": "SS 2024"},
                ],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"pdf-bytes")

        mock_student_repo.upsert.assert_called_once()
        call_kwargs = mock_student_repo.upsert.call_args.kwargs
        assert len(call_kwargs["courses"]) == 2

    async def test_computes_gpa_from_courses(self, student_service, mock_student_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": None,
                "courses": [
                    {"course_name": "A", "credits": 5.0, "grade": "1,0"},
                    {"course_name": "B", "credits": 5.0, "grade": "3,0"},
                ],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"pdf-bytes")

        call_kwargs = mock_student_repo.upsert.call_args.kwargs
        assert call_kwargs["gpa"] == 2.0

    async def test_embeds_concatenated_courses(self, student_service, mock_student_repo, mock_llm_chat, mock_llm_embed):
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": None,
                "courses": [
                    {"course_name": "Machine Learning", "credits": 5.0, "grade": "1,3"},
                    {"course_name": "Databases", "credits": 6.0, "grade": "2,0"},
                ],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"pdf-bytes")

        mock_llm_embed.embed.assert_called_once()
        embed_text = mock_llm_embed.embed.call_args[0][1]
        assert "Machine Learning (5.0 ECTS)" in embed_text
        assert "Databases (6.0 ECTS)" in embed_text

    async def test_upserts_profile(self, student_service, mock_student_repo, mock_llm_chat):
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": None,
                "courses": [{"course_name": "ML", "credits": 5.0, "grade": "1,0"}],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(user_id=1, pdf_bytes=b"pdf", program="CS", semester=4)

        mock_student_repo.upsert.assert_called_once()
        call_kwargs = mock_student_repo.upsert.call_args.kwargs
        assert call_kwargs["program"] == "CS"
        assert call_kwargs["semester"] == 4
        mock_student_repo.commit.assert_called_once()

    async def test_empty_courses_saves_with_none_gpa(self, student_service, mock_student_repo, mock_llm_chat):
        """When LLM returns 0 courses, the empty list passes strict validation
        and the profile is saved with GPA=None and no courses."""
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": None,
                "courses": [],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"pdf-bytes")

        call_kwargs = mock_student_repo.upsert.call_args.kwargs
        assert call_kwargs["gpa"] is None
        assert len(call_kwargs["courses"]) == 0

    async def test_skips_invalid_course_rows(self, student_service, mock_student_repo, mock_llm_chat):
        """Strict validation fails due to the invalid row, falls back to
        per-course validation. The valid course survives."""
        mock_llm_chat.chat.return_value = _llm_json_response(
            {
                "gpa": None,
                "courses": [
                    {"course_name": "Valid Course", "credits": 5.0, "grade": "1,3"},
                    {"course_name": "", "credits": 5.0, "grade": "2,0"},
                ],
            }
        )
        mock_student_repo.upsert.return_value = _make_student()
        mock_student_repo.get_by_user_id.return_value = _make_student()

        await student_service.upload_transcript(1, b"pdf-bytes")

        call_kwargs = mock_student_repo.upsert.call_args.kwargs
        assert len(call_kwargs["courses"]) >= 1

    async def test_empty_pdf_text_raises(self, student_service):
        self._extract_mock.return_value = "   "

        with pytest.raises(BadRequestException, match="Could not extract text"):
            await student_service.upload_transcript(1, b"empty-pdf")
