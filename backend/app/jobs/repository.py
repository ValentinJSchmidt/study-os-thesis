"""Data-access layer for the jobs table."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus, JobType


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        type: JobType,
        user_id: int,
        input_data: dict[str, Any] | None = None,
        celery_task_id: str | None = None,
    ) -> Job:
        job = Job(
            type=type,
            user_id=user_id,
            input_data=input_data,
            celery_task_id=celery_task_id,
            status=JobStatus.pending,
            attempts=0,
        )
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        await self._session.commit()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        return await self._session.get(Job, job_id)

    async def update(self, job: Job, **fields: Any) -> Job:
        for k, v in fields.items():
            setattr(job, k, v)
        await self._session.flush()
        await self._session.refresh(job)
        await self._session.commit()
        return job

    async def list_by_user(
        self,
        user_id: int,
        *,
        type: JobType | None = None,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        stmt = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc()).limit(limit).offset(offset)
        if type is not None:
            stmt = stmt.where(Job.type == type)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        rows = await self._session.scalars(stmt)
        return list(rows)

    async def commit(self) -> None:
        await self._session.commit()
