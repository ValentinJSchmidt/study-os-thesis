"""Unit tests for ThesisService."""

from __future__ import annotations

import pytest

from app.exceptions import BadRequestException, NotFoundException
from app.models import Thesis, ThesisSource, User, UserRole
from app.theses.schemas import ThesisCreate
from app.theses.service import ThesisService
from tests.conftest import _make_orm


@pytest.fixture
def thesis_service(
    mock_thesis_repo,
    mock_user_repo,
    mock_llm_embed,
    fake_settings,
) -> ThesisService:
    return ThesisService(mock_thesis_repo, mock_user_repo, mock_llm_embed, fake_settings)


def _make_thesis(**overrides) -> Thesis:
    defaults = dict(id=1, title="Test", abstract="Abstract", submitter_id=1, source=ThesisSource.professor, embedding=[0.1] * 10)
    return _make_orm(Thesis, **{**defaults, **overrides})


@pytest.mark.unit
class TestCreateThesis:
    async def test_embeds_title_and_abstract(self, thesis_service, mock_llm_embed, mock_thesis_repo, fake_admin):
        mock_thesis_repo.create.return_value = _make_thesis()
        data = ThesisCreate(title="My Title", abstract="My long abstract text here.")

        await thesis_service.create_thesis(data, fake_admin)

        mock_llm_embed.embed.assert_called_once_with("test-embed-model", "My Title\n\nMy long abstract text here.")

    async def test_admin_sets_source_professor(self, thesis_service, mock_thesis_repo, fake_admin):
        mock_thesis_repo.create.return_value = _make_thesis()
        data = ThesisCreate(title="Title Here", abstract="Abstract text long enough.")

        await thesis_service.create_thesis(data, fake_admin)

        call_kwargs = mock_thesis_repo.create.call_args.kwargs
        assert call_kwargs["source"] == ThesisSource.professor

    async def test_student_sets_source_student(self, thesis_service, mock_thesis_repo, fake_user):
        mock_thesis_repo.create.return_value = _make_thesis()
        data = ThesisCreate(title="Title Here", abstract="Abstract text long enough.")

        await thesis_service.create_thesis(data, fake_user)

        call_kwargs = mock_thesis_repo.create.call_args.kwargs
        assert call_kwargs["source"] == ThesisSource.student

    async def test_supervisor_validates_exists(self, thesis_service, mock_user_repo, fake_admin):
        mock_user_repo.get_by_id.return_value = None
        data = ThesisCreate(
            title="Title Here",
            abstract="Abstract text long enough.",
            supervisor_id=99,
        )

        with pytest.raises(BadRequestException, match="supervisor_id must reference an admin"):
            await thesis_service.create_thesis(data, fake_admin)

    async def test_supervisor_validates_is_admin(self, thesis_service, mock_user_repo, fake_admin):
        student_supervisor = _make_orm(User, id=99, role=UserRole.student)
        mock_user_repo.get_by_id.return_value = student_supervisor

        data = ThesisCreate(
            title="Title Here",
            abstract="Abstract text long enough.",
            supervisor_id=99,
        )

        with pytest.raises(BadRequestException, match="supervisor_id must reference an admin"):
            await thesis_service.create_thesis(data, fake_admin)

    async def test_persists_and_commits(self, thesis_service, mock_thesis_repo, fake_admin):
        mock_thesis_repo.create.return_value = _make_thesis()
        data = ThesisCreate(title="Title Here", abstract="Abstract text long enough.")

        await thesis_service.create_thesis(data, fake_admin)

        mock_thesis_repo.create.assert_called_once()
        mock_thesis_repo.commit.assert_called_once()

    async def test_embed_false_skips_embedding(self, thesis_service, mock_llm_embed, mock_thesis_repo, fake_admin):
        """With embed=False the controller defers embedding to the worker."""
        mock_thesis_repo.create.return_value = _make_thesis()
        data = ThesisCreate(title="Title Here", abstract="Abstract text long enough.")

        await thesis_service.create_thesis(data, fake_admin, embed=False)

        mock_llm_embed.embed.assert_not_called()
        assert mock_thesis_repo.create.call_args.kwargs["embedding"] is None


@pytest.mark.unit
class TestListTheses:
    async def test_passes_limit_and_offset(self, thesis_service, mock_thesis_repo):
        mock_thesis_repo.list.return_value = []

        await thesis_service.list_theses(limit=10, offset=5)

        mock_thesis_repo.list.assert_called_once_with(limit=10, offset=5)


@pytest.mark.unit
class TestGetThesis:
    async def test_returns_thesis(self, thesis_service, mock_thesis_repo):
        expected = _make_thesis(id=42)
        mock_thesis_repo.get_by_id.return_value = expected

        result = await thesis_service.get_thesis(42)

        assert result.id == 42
        mock_thesis_repo.get_by_id.assert_called_once_with(42)

    async def test_not_found_raises(self, thesis_service, mock_thesis_repo):
        mock_thesis_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await thesis_service.get_thesis(999)
