"""Tests for chair-related Celery tasks (ArXiv ingest + description embedding)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chairs.tasks import (
    _embed_chair_work,
    _ingest_arxiv_work,
    embed_chair_description,
    ingest_arxiv_paper,
)
from app.exceptions import AlreadyExistsException, NotFoundException


def _acm(session):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.mark.unit
class TestIngestArxivWiring:
    def test_treats_duplicate_and_missing_as_permanent(self):
        with patch("app.chairs.tasks.execute_task") as ex:
            ingest_arxiv_paper(chair_id=1, arxiv_id="2301.07041", user_id=3, job_id="j")

        permanent = ex.call_args.kwargs["permanent_exceptions"]
        assert AlreadyExistsException in permanent
        assert NotFoundException in permanent


@pytest.mark.unit
class TestEmbedChairWiring:
    def test_delegates_to_runner(self):
        with patch("app.chairs.tasks.execute_task") as ex:
            embed_chair_description(chair_id=1, user_id=3, job_id="j")
        assert ex.call_args.kwargs["job_id"] == "j"
        assert callable(ex.call_args.kwargs["work"])


@pytest.mark.unit
class TestIngestArxivWork:
    async def test_calls_service_and_returns_doc(self):
        session = AsyncMock()
        svc = AsyncMock()
        svc.ingest_arxiv_paper.return_value = SimpleNamespace(id=42, title="Paper")
        settings = SimpleNamespace(ollama_embed_model="m")

        with (
            patch("app.db.SessionLocal", return_value=_acm(session)),
            patch("app.chairs.repository.ChairRepository", return_value=AsyncMock()),
            patch("app.chairs.service.ChairService", return_value=svc),
            patch("app.llm.factory.build_embed_client", return_value=AsyncMock()),
        ):
            result = await _ingest_arxiv_work(1, "2301.07041", settings)

        svc.ingest_arxiv_paper.assert_awaited_once()
        assert result == {"document_id": 42, "title": "Paper"}


@pytest.mark.unit
class TestEmbedChairWork:
    async def test_stores_description_document(self):
        session = AsyncMock()
        chair = SimpleNamespace(short_description="A research chair.")
        repo = AsyncMock()
        repo.get_by_id.return_value = chair
        embed_client = AsyncMock()
        embed_client.embed.return_value = [0.2] * 4
        settings = SimpleNamespace(ollama_embed_model="m")

        with (
            patch("app.db.SessionLocal", return_value=_acm(session)),
            patch("app.chairs.repository.ChairRepository", return_value=repo),
            patch("app.llm.factory.build_embed_client", return_value=embed_client),
        ):
            from app.models.chair import ChairDocumentKind

            result = await _embed_chair_work(1, settings)

        repo.add_document.assert_awaited_once()
        kw = repo.add_document.call_args.kwargs
        assert kw["kind"] == ChairDocumentKind.description
        assert kw["content"] == "A research chair."
        assert kw["embedding"] == [0.2] * 4
        assert result == {"chair_id": 1}

    async def test_missing_chair_raises_not_found(self):
        session = AsyncMock()
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        settings = SimpleNamespace(ollama_embed_model="m")

        with (
            patch("app.db.SessionLocal", return_value=_acm(session)),
            patch("app.chairs.repository.ChairRepository", return_value=repo),
            patch("app.llm.factory.build_embed_client", return_value=AsyncMock()),
        ):
            with pytest.raises(NotFoundException):
                await _embed_chair_work(404, settings)
