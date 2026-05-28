"""Tests for the transcript parsing Celery task."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import BadRequestException, NotFoundException
from app.students.tasks import _parse_transcript_work, parse_transcript


def _acm(session):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.mark.unit
class TestParseTranscriptWiring:
    def test_treats_bad_request_and_missing_as_permanent(self):
        with patch("app.students.tasks.execute_task") as ex:
            parse_transcript(user_id=1, job_id="j", program="CS", semester=4)

        permanent = ex.call_args.kwargs["permanent_exceptions"]
        assert BadRequestException in permanent
        assert NotFoundException in permanent


@pytest.mark.unit
class TestParseTranscriptWork:
    async def test_fetches_pdf_and_processes(self):
        session = AsyncMock()
        svc = AsyncMock()
        svc.upload_transcript.return_value = SimpleNamespace(courses=[1, 2, 3])
        settings = SimpleNamespace(redis_url="redis://x", ollama_embed_model="m")

        with (
            patch("app.students.pdf_store.fetch_pdf", AsyncMock(return_value=b"PDFBYTES")) as fetch,
            patch("app.students.pdf_store.delete_pdf", AsyncMock()) as delete,
            patch("app.db.SessionLocal", return_value=_acm(session)),
            patch("app.students.repository.StudentRepository", return_value=AsyncMock()),
            patch("app.students.service.StudentService", return_value=svc),
            patch("app.llm.factory.build_chat_client", return_value=AsyncMock()),
            patch("app.llm.factory.build_embed_client", return_value=AsyncMock()),
        ):
            result = await _parse_transcript_work(1, "job-1", settings, "CS", 4)

        fetch.assert_awaited_once_with("redis://x", "job-1")
        svc.upload_transcript.assert_awaited_once_with(1, b"PDFBYTES", program="CS", semester=4)
        delete.assert_awaited_once_with("redis://x", "job-1")
        assert result == {"user_id": 1, "courses": 3}

    async def test_missing_pdf_raises_bad_request(self):
        settings = SimpleNamespace(redis_url="redis://x", ollama_embed_model="m")

        with patch("app.students.pdf_store.fetch_pdf", AsyncMock(return_value=None)):
            with pytest.raises(BadRequestException):
                await _parse_transcript_work(1, "job-1", settings, None, None)
