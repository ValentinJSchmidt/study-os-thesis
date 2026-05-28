"""Tests for the thesis embedding Celery task.

Covers two layers: the task wiring (delegates to the shared runner with the
right config) and the actual unit of work (embeds title+abstract, sets the
embedding, raises NotFound for a missing thesis).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import NotFoundException
from app.theses.tasks import _embed_thesis_work, embed_thesis


def _acm(session):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.mark.unit
class TestEmbedThesisWiring:
    def test_delegates_to_runner(self):
        with patch("app.theses.tasks.execute_task") as ex:
            ex.return_value = {"ok": 1}
            out = embed_thesis(thesis_id=5, user_id=9, job_id="job-x")

        assert out == {"ok": 1}
        kw = ex.call_args.kwargs
        assert kw["job_id"] == "job-x"
        assert kw["user_id"] == 9
        assert kw["redis_url"]
        assert callable(kw["work"])
        # default success event / no started event for embedding tasks
        assert "started_event" not in kw


@pytest.mark.unit
class TestEmbedThesisWork:
    async def test_embeds_title_and_abstract(self):
        session = AsyncMock()
        thesis = SimpleNamespace(title="My Title", abstract="My Abstract", embedding=None)
        repo = AsyncMock()
        repo.get_by_id.return_value = thesis
        embed_client = AsyncMock()
        embed_client.embed.return_value = [0.1] * 8
        settings = SimpleNamespace(ollama_embed_model="embed-model")

        with (
            patch("app.db.SessionLocal", return_value=_acm(session)),
            patch("app.theses.repository.ThesisRepository", return_value=repo),
            patch("app.llm.factory.build_embed_client", return_value=embed_client),
        ):
            result = await _embed_thesis_work(1, settings)

        embed_client.embed.assert_awaited_once_with("embed-model", "My Title\n\nMy Abstract")
        assert thesis.embedding == [0.1] * 8
        assert result == {"thesis_id": 1, "dim": 8}
        session.commit.assert_awaited_once()

    async def test_missing_thesis_raises_not_found(self):
        session = AsyncMock()
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        settings = SimpleNamespace(ollama_embed_model="m")

        with (
            patch("app.db.SessionLocal", return_value=_acm(session)),
            patch("app.theses.repository.ThesisRepository", return_value=repo),
            patch("app.llm.factory.build_embed_client", return_value=AsyncMock()),
        ):
            with pytest.raises(NotFoundException):
                await _embed_thesis_work(999, settings)
