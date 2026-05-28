"""Phase 2: Tests for JobService.

These tests will FAIL until app.jobs.service is implemented.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_job_repo():
    return AsyncMock()


@pytest.fixture
def job_service(mock_job_repo):
    from app.jobs.service import JobService

    return JobService(mock_job_repo)


def _make_job(**overrides):
    from app.models.job import JobStatus, JobType

    defaults = dict(
        id=uuid.uuid4(),
        type=JobType.embed_thesis,
        status=JobStatus.pending,
        user_id=1,
        celery_task_id="celery-abc",
        input_data={"thesis_id": 5},
        result_data=None,
        error=None,
        attempts=0,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        started_at=None,
        completed_at=None,
    )
    return SimpleNamespace(**{**defaults, **overrides})


@pytest.mark.unit
class TestCreateJob:
    async def test_sets_pending_status(self, job_service, mock_job_repo):
        from app.models.job import JobStatus, JobType

        mock_job_repo.create.return_value = _make_job()

        result = await job_service.create_job(
            type=JobType.embed_thesis,
            user_id=1,
            input_data={"thesis_id": 5},
            celery_task_id="abc",
        )

        assert result.status == JobStatus.pending

    async def test_stores_input_data(self, job_service, mock_job_repo):
        from app.models.job import JobType

        mock_job_repo.create.return_value = _make_job(input_data={"thesis_id": 5})

        result = await job_service.create_job(
            type=JobType.embed_thesis,
            user_id=1,
            input_data={"thesis_id": 5},
            celery_task_id="abc",
        )

        assert result.input_data == {"thesis_id": 5}

    async def test_assigns_user_id(self, job_service, mock_job_repo):
        from app.models.job import JobType

        mock_job_repo.create.return_value = _make_job(user_id=42)

        result = await job_service.create_job(
            type=JobType.embed_thesis,
            user_id=42,
            input_data={},
            celery_task_id="abc",
        )

        assert result.user_id == 42

    async def test_stores_celery_task_id(self, job_service, mock_job_repo):
        from app.models.job import JobType

        mock_job_repo.create.return_value = _make_job(celery_task_id="celery-xyz")

        result = await job_service.create_job(
            type=JobType.embed_thesis,
            user_id=1,
            input_data={},
            celery_task_id="celery-xyz",
        )

        assert result.celery_task_id == "celery-xyz"


@pytest.mark.unit
class TestMarkStatus:
    async def test_mark_started(self, job_service, mock_job_repo):
        from app.models.job import JobStatus

        job = _make_job()
        mock_job_repo.get_by_id.return_value = job
        mock_job_repo.update.return_value = _make_job(
            status=JobStatus.started,
            started_at=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        )

        result = await job_service.mark_started(job.id)

        assert result.status == JobStatus.started
        assert result.started_at is not None

    async def test_mark_success(self, job_service, mock_job_repo):
        from app.models.job import JobStatus

        job = _make_job()
        mock_job_repo.get_by_id.return_value = job
        mock_job_repo.update.return_value = _make_job(
            status=JobStatus.success,
            result_data={"count": 3},
            completed_at=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        )

        result = await job_service.mark_success(job.id, result_data={"count": 3})

        assert result.status == JobStatus.success
        assert result.result_data == {"count": 3}
        assert result.completed_at is not None

    async def test_mark_failure(self, job_service, mock_job_repo):
        from app.models.job import JobStatus

        job = _make_job()
        mock_job_repo.get_by_id.return_value = job
        mock_job_repo.update.return_value = _make_job(
            status=JobStatus.failure,
            error="traceback here",
            completed_at=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        )

        result = await job_service.mark_failure(job.id, error="traceback here")

        assert result.status == JobStatus.failure
        assert result.error == "traceback here"
        assert result.completed_at is not None

    async def test_mark_retry_increments_attempts(self, job_service, mock_job_repo):
        from app.models.job import JobStatus

        job = _make_job(attempts=0)
        mock_job_repo.get_by_id.return_value = job
        mock_job_repo.update.return_value = _make_job(status=JobStatus.retry, attempts=1)

        result = await job_service.mark_retry(job.id)

        assert result.attempts == 1
        assert result.status == JobStatus.retry


@pytest.mark.unit
class TestGetJob:
    async def test_returns_job_for_owner(self, job_service, mock_job_repo):
        job = _make_job(user_id=1)
        mock_job_repo.get_by_id.return_value = job

        result = await job_service.get_job(job.id, user_id=1)

        assert result.id == job.id

    async def test_raises_not_found_for_wrong_user(self, job_service, mock_job_repo):
        from app.exceptions import NotFoundException

        job = _make_job(user_id=99)
        mock_job_repo.get_by_id.return_value = job

        with pytest.raises(NotFoundException):
            await job_service.get_job(job.id, user_id=1)

    async def test_raises_not_found_for_missing_id(self, job_service, mock_job_repo):
        from app.exceptions import NotFoundException

        mock_job_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await job_service.get_job(uuid.uuid4(), user_id=1)


@pytest.mark.unit
class TestListJobs:
    async def test_returns_only_user_jobs(self, job_service, mock_job_repo):
        mock_job_repo.list_by_user.return_value = [_make_job(user_id=1)]

        result = await job_service.list_jobs(user_id=1)

        mock_job_repo.list_by_user.assert_called_once()
        assert len(result) == 1

    async def test_filters_by_type(self, job_service, mock_job_repo):
        from app.models.job import JobType

        mock_job_repo.list_by_user.return_value = []

        await job_service.list_jobs(user_id=1, type=JobType.embed_thesis)

        call_kwargs = mock_job_repo.list_by_user.call_args
        assert call_kwargs.kwargs.get("type") == JobType.embed_thesis or (len(call_kwargs.args) > 1 and call_kwargs.args[1] == JobType.embed_thesis)

    async def test_filters_by_status(self, job_service, mock_job_repo):
        from app.models.job import JobStatus

        mock_job_repo.list_by_user.return_value = []

        await job_service.list_jobs(user_id=1, status=JobStatus.pending)

        call_kwargs = mock_job_repo.list_by_user.call_args
        assert call_kwargs.kwargs.get("status") == JobStatus.pending or (len(call_kwargs.args) > 2 and call_kwargs.args[2] == JobStatus.pending)


@pytest.mark.unit
class TestSetCeleryTaskId:
    async def test_updates_task_id(self, job_service, mock_job_repo):
        job = _make_job(celery_task_id=None)
        mock_job_repo.get_by_id.return_value = job
        mock_job_repo.update.return_value = job

        await job_service.set_celery_task_id(job.id, "celery-xyz")

        mock_job_repo.update.assert_called_once()
        assert mock_job_repo.update.call_args.kwargs["celery_task_id"] == "celery-xyz"

    async def test_missing_job_raises(self, job_service, mock_job_repo):
        from app.exceptions import NotFoundException

        mock_job_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await job_service.set_celery_task_id(uuid.uuid4(), "celery-xyz")
