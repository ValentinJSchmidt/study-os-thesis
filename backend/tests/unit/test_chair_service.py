"""Unit tests for ChairService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.chairs.schemas import ArxivIngestRequest, ChairCreate, ChairPatch
from app.chairs.service import ChairService
from app.exceptions import AlreadyExistsException, NotFoundException
from app.models.chair import Chair, ChairDocument, ChairDocumentKind
from tests.conftest import _make_orm


@pytest.fixture
def chair_service(mock_chair_repo, mock_llm_embed, fake_settings) -> ChairService:
    return ChairService(mock_chair_repo, mock_llm_embed, fake_settings)


def _make_chair(**overrides) -> Chair:
    defaults = dict(id=1, name="Test Chair", short_description="A test chair description.", professor_name="Prof. Test", professor_user_id=None, website_url=None)
    return _make_orm(Chair, **{**defaults, **overrides})


def _make_document(**overrides) -> ChairDocument:
    defaults = dict(id=1, chair_id=1, kind=ChairDocumentKind.paper, title="Paper", content="Abstract", arxiv_id="2301.07041", published_year=2023, embedding=[0.1] * 10)
    return _make_orm(ChairDocument, **{**defaults, **overrides})


@pytest.mark.unit
class TestCreateChair:
    async def test_embeds_description(self, chair_service, mock_llm_embed, mock_chair_repo):
        chair = _make_chair()
        mock_chair_repo.create.return_value = chair
        mock_chair_repo.get_by_id.return_value = chair
        mock_chair_repo.add_document.return_value = _make_document()

        data = ChairCreate(
            name="New Chair",
            short_description="Description that is long enough for validation.",
            professor_name="Prof. New",
        )
        await chair_service.create_chair(data)

        mock_llm_embed.embed.assert_called_once_with(
            "test-embed-model",
            "Description that is long enough for validation.",
        )

    async def test_stores_description_document(self, chair_service, mock_chair_repo, mock_llm_embed):
        chair = _make_chair()
        mock_chair_repo.create.return_value = chair
        mock_chair_repo.get_by_id.return_value = chair
        mock_chair_repo.add_document.return_value = _make_document()

        data = ChairCreate(
            name="Chair",
            short_description="Description that is long enough for validation.",
            professor_name="Prof.",
        )
        await chair_service.create_chair(data)

        mock_chair_repo.add_document.assert_called_once()
        call_kwargs = mock_chair_repo.add_document.call_args.kwargs
        assert call_kwargs["kind"] == ChairDocumentKind.description
        assert call_kwargs["content"] == "Description that is long enough for validation."

    async def test_embed_failure_still_creates_chair(self, chair_service, mock_chair_repo, mock_llm_embed):
        chair = _make_chair()
        mock_chair_repo.create.return_value = chair
        mock_chair_repo.get_by_id.return_value = chair
        mock_chair_repo.add_document.return_value = _make_document()
        mock_llm_embed.embed.side_effect = Exception("LLM down")

        data = ChairCreate(
            name="Chair",
            short_description="Description that is long enough for validation.",
            professor_name="Prof.",
        )
        result = await chair_service.create_chair(data)

        assert result is not None
        call_kwargs = mock_chair_repo.add_document.call_args.kwargs
        assert call_kwargs["embedding"] is None

    async def test_embed_false_skips_embedding_and_document(self, chair_service, mock_chair_repo, mock_llm_embed):
        """With embed=False the worker creates the description document instead."""
        chair = _make_chair()
        mock_chair_repo.create.return_value = chair
        mock_chair_repo.get_by_id.return_value = chair

        data = ChairCreate(
            name="Chair",
            short_description="Description that is long enough for validation.",
            professor_name="Prof.",
        )
        await chair_service.create_chair(data, embed=False)

        mock_llm_embed.embed.assert_not_called()
        mock_chair_repo.add_document.assert_not_called()
        mock_chair_repo.commit.assert_called_once()


@pytest.mark.unit
class TestIngestArxiv:
    async def test_validates_chair_exists(self, chair_service, mock_chair_repo):
        mock_chair_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            req = ArxivIngestRequest(arxiv_id="2301.07041")
            await chair_service.ingest_arxiv_paper(999, req)

    async def test_duplicate_raises(self, chair_service, mock_chair_repo):
        mock_chair_repo.get_by_id.return_value = _make_chair()
        mock_chair_repo.get_document_by_arxiv.return_value = _make_document()

        with pytest.raises(AlreadyExistsException):
            req = ArxivIngestRequest(arxiv_id="2301.07041")
            await chair_service.ingest_arxiv_paper(1, req)

    async def test_fetches_metadata(self, chair_service, mock_chair_repo, monkeypatch):
        mock_chair_repo.get_by_id.return_value = _make_chair()
        mock_chair_repo.get_document_by_arxiv.return_value = None
        mock_chair_repo.add_document.return_value = _make_document()

        fetch_mock = AsyncMock(return_value=("Title", "Abstract text", 2024))
        monkeypatch.setattr("app.chairs.service._fetch_arxiv_metadata", fetch_mock)

        req = ArxivIngestRequest(arxiv_id="2301.07041")
        await chair_service.ingest_arxiv_paper(1, req)

        fetch_mock.assert_called_once_with("2301.07041")

    async def test_embeds_abstract(self, chair_service, mock_chair_repo, mock_llm_embed, monkeypatch):
        mock_chair_repo.get_by_id.return_value = _make_chair()
        mock_chair_repo.get_document_by_arxiv.return_value = None
        mock_chair_repo.add_document.return_value = _make_document()

        monkeypatch.setattr(
            "app.chairs.service._fetch_arxiv_metadata",
            AsyncMock(return_value=("Title", "The paper abstract.", 2024)),
        )

        req = ArxivIngestRequest(arxiv_id="2301.07041")
        await chair_service.ingest_arxiv_paper(1, req)

        mock_llm_embed.embed.assert_called_once_with("test-embed-model", "The paper abstract.")

    async def test_stores_paper_document(self, chair_service, mock_chair_repo, monkeypatch):
        mock_chair_repo.get_by_id.return_value = _make_chair()
        mock_chair_repo.get_document_by_arxiv.return_value = None
        mock_chair_repo.add_document.return_value = _make_document()

        monkeypatch.setattr(
            "app.chairs.service._fetch_arxiv_metadata",
            AsyncMock(return_value=("Paper Title", "Paper Abstract", 2023)),
        )

        req = ArxivIngestRequest(arxiv_id="2301.07041")
        await chair_service.ingest_arxiv_paper(1, req)

        call_kwargs = mock_chair_repo.add_document.call_args.kwargs
        assert call_kwargs["kind"] == ChairDocumentKind.paper
        assert call_kwargs["title"] == "Paper Title"
        assert call_kwargs["content"] == "Paper Abstract"
        assert call_kwargs["arxiv_id"] == "2301.07041"
        assert call_kwargs["published_year"] == 2023


@pytest.mark.unit
class TestDeleteChair:
    async def test_delegates_to_repo(self, chair_service, mock_chair_repo):
        chair = _make_chair()
        mock_chair_repo.get_by_id.return_value = chair

        await chair_service.delete_chair(1)

        mock_chair_repo.delete.assert_called_once_with(chair)
        mock_chair_repo.commit.assert_called_once()

    async def test_not_found_raises(self, chair_service, mock_chair_repo):
        mock_chair_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await chair_service.delete_chair(999)


@pytest.mark.unit
class TestUpdateChair:
    async def test_patches_fields(self, chair_service, mock_chair_repo):
        chair = _make_chair()
        mock_chair_repo.get_by_id.return_value = chair
        mock_chair_repo.update.return_value = chair

        data = ChairPatch(name="Updated Name")
        await chair_service.update_chair(1, data)

        mock_chair_repo.update.assert_called_once()


@pytest.mark.unit
class TestGetChair:
    async def test_not_found_raises(self, chair_service, mock_chair_repo):
        mock_chair_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await chair_service.get_chair(999)
