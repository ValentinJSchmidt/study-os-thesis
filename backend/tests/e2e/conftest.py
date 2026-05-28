"""E2E test fixtures: FastAPI app with dependency overrides.

Overrides service-level dependencies so controllers execute real logic
against mock services, without needing a database or LLM provider.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models import EMBEDDING_DIM, UserRole


def _make_user(user_id: int, email: str, role: UserRole) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        email=email,
        role=role,
        password_hash="fake-hash",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


_student_user = _make_user(1, "student@test.com", UserRole.student)
_admin_user = _make_user(2, "admin@test.com", UserRole.admin)


def _mock_llm() -> AsyncMock:
    mock = AsyncMock()
    mock.chat.return_value = {"message": {"role": "assistant", "content": "OK", "tool_calls": []}}
    mock.embed.return_value = [0.1] * EMBEDDING_DIM
    mock.aclose.return_value = None
    return mock


def _make_fake_job(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        type="embed_thesis",
        status="pending",
        user_id=1,
        celery_task_id="celery-test-id",
        input_data={},
        result_data=None,
        error=None,
        attempts=0,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        started_at=None,
        completed_at=None,
    )
    return SimpleNamespace(**{**defaults, **overrides})


def _mock_job_service():
    """Return a mock JobService whose create_job returns a fake Job."""
    svc = AsyncMock()
    svc.create_job.return_value = _make_fake_job()
    svc.get_job.return_value = _make_fake_job()
    svc.list_jobs.return_value = []
    return svc


def _mock_thesis_service():
    svc = AsyncMock()
    fake_thesis = SimpleNamespace(
        id=1,
        title="Test",
        abstract="Abstract",
        chair_id=None,
        supervisor_id=None,
        submitter_id=2,
        source="professor",
        difficulty=None,
        skills_required=None,
        generated_for_user_id=None,
        chat_session_id=None,
        embedding=None,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    svc.create_thesis.return_value = fake_thesis
    svc.list_theses.return_value = []
    svc.get_thesis.return_value = fake_thesis
    return svc


def _mock_chair_service():
    svc = AsyncMock()
    fake_chair = SimpleNamespace(
        id=1,
        name="Chair",
        short_description="Desc",
        professor_name="Prof",
        professor_user_id=None,
        website_url=None,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        documents=[],
    )
    svc.create_chair.return_value = fake_chair
    svc.list_chairs.return_value = []
    svc.get_chair.return_value = fake_chair
    svc.update_chair.return_value = fake_chair
    svc.delete_chair.return_value = None
    svc.ingest_arxiv_paper.return_value = SimpleNamespace(
        id=1,
        kind="paper",
        title="Paper",
        content="Abstract",
        arxiv_id="2301.07041",
        published_year=2023,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    svc.delete_document.return_value = None
    return svc


def _mock_student_service():
    svc = AsyncMock()
    fake_profile = SimpleNamespace(
        user_id=1,
        program="CS",
        semester=4,
        gpa=1.7,
        updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        courses=[],
    )
    svc.get_profile.return_value = fake_profile
    svc.upload_transcript.return_value = fake_profile
    return svc


def _mock_chat_service():
    svc = AsyncMock()
    fake_session = SimpleNamespace(
        id=1,
        user_id=1,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    svc.create_session.return_value = fake_session
    svc.list_sessions.return_value = []
    svc.get_messages.return_value = []
    svc.send_message.return_value = []
    # The controller accesses _chat_repo.get_session directly for ownership check
    svc._chat_repo = AsyncMock()
    svc._chat_repo.get_session.return_value = fake_session
    return svc


def _mock_celery_task():
    """Return a MagicMock that behaves like a Celery AsyncResult."""
    result = MagicMock()
    result.id = "celery-task-" + uuid.uuid4().hex[:8]
    return result


@pytest.fixture(scope="session")
def _app():
    """Create the FastAPI app with all dependency overrides."""
    import os

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5433/test")
    os.environ.setdefault("JWT_SECRET", "test-secret-for-e2e-tests-1234567890")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

    from app.main import create_app

    app = create_app()

    # Set app.state for deps that read from it
    app.state.llm_chat_client = _mock_llm()
    app.state.llm_embed_client = _mock_llm()
    app.state.llm_available = True

    from app.ws.manager import ConnectionManager

    app.state.ws_manager = ConnectionManager()

    return app


@pytest.fixture(autouse=True)
def _override_deps(_app):
    """Override DI for each test so we get fresh mocks."""
    from app.auth.deps import get_current_user
    from app.theses.deps import get_thesis_service
    from app.chairs.deps import get_chair_service
    from app.students.deps import get_student_service
    from app.chat.deps import get_chat_service
    from app.jobs.deps import get_job_service

    _app.dependency_overrides[get_current_user] = lambda: _student_user
    _app.dependency_overrides[get_thesis_service] = _mock_thesis_service
    _app.dependency_overrides[get_chair_service] = _mock_chair_service
    _app.dependency_overrides[get_student_service] = _mock_student_service
    _app.dependency_overrides[get_chat_service] = _mock_chat_service
    _app.dependency_overrides[get_job_service] = _mock_job_service

    yield

    _app.dependency_overrides.clear()


@pytest.fixture
def _celery_patch():
    """Patch all Celery .delay() calls so tasks don't actually run.

    Also patches the transcript PDF store so e2e tests don't require a live
    Redis instance.
    """
    with (
        patch("app.theses.tasks.embed_thesis.delay", return_value=_mock_celery_task()) as t,
        patch("app.chairs.tasks.embed_chair_description.delay", return_value=_mock_celery_task()) as c1,
        patch("app.chairs.tasks.ingest_arxiv_paper.delay", return_value=_mock_celery_task()) as c2,
        patch("app.students.tasks.parse_transcript.delay", return_value=_mock_celery_task()) as s,
        patch("app.chat.tasks.process_chat_turn.delay", return_value=_mock_celery_task()) as ch,
        patch("app.students.pdf_store.store_pdf", new=AsyncMock()),
    ):
        yield {
            "embed_thesis": t,
            "embed_chair_description": c1,
            "ingest_arxiv_paper": c2,
            "parse_transcript": s,
            "process_chat_turn": ch,
        }


@pytest.fixture
async def client(_app, _celery_patch) -> AsyncIterator[AsyncClient]:
    """HTTP client authenticated as a student user."""
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def admin_client(_app, _celery_patch) -> AsyncIterator[AsyncClient]:
    """HTTP client authenticated as an admin user."""
    from app.auth.deps import get_current_user

    _app.dependency_overrides[get_current_user] = lambda: _admin_user
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    _app.dependency_overrides[get_current_user] = lambda: _student_user
