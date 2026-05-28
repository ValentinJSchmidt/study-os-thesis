"""Phase 2: Tests for Job schemas and enums.

These tests will FAIL until app.models.job and app.jobs.schemas are implemented.
"""

import uuid

import pytest


@pytest.mark.unit
class TestJobEnums:
    def test_job_type_enum_has_all_values(self):
        from app.models.job import JobType

        expected = {"embed_thesis", "embed_chair", "ingest_arxiv", "parse_transcript", "chat_turn", "generate_proposal"}
        actual = {e.value for e in JobType}
        assert expected == actual

    def test_job_status_enum_has_all_values(self):
        from app.models.job import JobStatus

        expected = {"pending", "started", "success", "failure", "retry"}
        actual = {e.value for e in JobStatus}
        assert expected == actual


@pytest.mark.unit
class TestJobOutSchema:
    def test_serializes_from_orm(self):
        from types import SimpleNamespace
        from datetime import datetime, timezone
        from app.jobs.schemas import JobOut
        from app.models.job import JobType, JobStatus

        fake_job = SimpleNamespace(
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

        result = JobOut.model_validate(fake_job, from_attributes=True)
        assert result.type == JobType.embed_thesis
        assert result.status == JobStatus.pending

    def test_includes_timestamps(self):
        from types import SimpleNamespace
        from datetime import datetime, timezone
        from app.jobs.schemas import JobOut
        from app.models.job import JobType, JobStatus

        now = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        fake_job = SimpleNamespace(
            id=uuid.uuid4(),
            type=JobType.chat_turn,
            status=JobStatus.success,
            user_id=1,
            celery_task_id=None,
            input_data=None,
            result_data={"count": 3},
            error=None,
            attempts=1,
            created_at=now,
            started_at=now,
            completed_at=now,
        )

        result = JobOut.model_validate(fake_job, from_attributes=True)
        assert result.created_at == now
        assert result.started_at == now
        assert result.completed_at == now

    def test_id_is_uuid(self):
        from types import SimpleNamespace
        from datetime import datetime, timezone
        from app.jobs.schemas import JobOut
        from app.models.job import JobType, JobStatus

        job_id = uuid.uuid4()
        fake_job = SimpleNamespace(
            id=job_id,
            type=JobType.embed_thesis,
            status=JobStatus.pending,
            user_id=1,
            celery_task_id=None,
            input_data=None,
            result_data=None,
            error=None,
            attempts=0,
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            started_at=None,
            completed_at=None,
        )

        result = JobOut.model_validate(fake_job, from_attributes=True)
        assert result.id == job_id
