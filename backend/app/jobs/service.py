"""Business logic for job lifecycle management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.exceptions import NotFoundException
from app.jobs.repository import JobRepository
from app.models.job import Job, JobStatus, JobType


class JobService:
    def __init__(self, job_repo: JobRepository) -> None:
        self._repo = job_repo

    async def create_job(
        self,
        *,
        type: JobType,
        user_id: int,
        input_data: dict[str, Any] | None = None,
        celery_task_id: str | None = None,
    ) -> Job:
        return await self._repo.create(
            type=type,
            user_id=user_id,
            input_data=input_data,
            celery_task_id=celery_task_id,
        )

    async def mark_started(self, job_id: uuid.UUID) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundException("Job", str(job_id))
        return await self._repo.update(
            job,
            status=JobStatus.started,
            started_at=datetime.now(timezone.utc),
        )

    async def mark_success(self, job_id: uuid.UUID, result_data: dict[str, Any] | None = None) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundException("Job", str(job_id))
        return await self._repo.update(
            job,
            status=JobStatus.success,
            result_data=result_data,
            completed_at=datetime.now(timezone.utc),
        )

    async def mark_failure(self, job_id: uuid.UUID, error: str) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundException("Job", str(job_id))
        return await self._repo.update(
            job,
            status=JobStatus.failure,
            error=error,
            completed_at=datetime.now(timezone.utc),
        )

    async def set_celery_task_id(self, job_id: uuid.UUID, celery_task_id: str) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundException("Job", str(job_id))
        return await self._repo.update(job, celery_task_id=celery_task_id)

    async def mark_retry(self, job_id: uuid.UUID) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundException("Job", str(job_id))
        return await self._repo.update(
            job,
            status=JobStatus.retry,
            attempts=job.attempts + 1,
        )

    async def get_job(self, job_id: uuid.UUID, user_id: int) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None or job.user_id != user_id:
            raise NotFoundException("Job", str(job_id))
        return job

    async def list_jobs(
        self,
        user_id: int,
        type: JobType | None = None,
        status: JobStatus | None = None,
    ) -> list[Job]:
        return await self._repo.list_by_user(user_id, type=type, status=status)
