"""HTTP endpoints for job status queries."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.auth.deps import CurrentUserDep
from app.jobs.deps import JobServiceDep
from app.jobs.schemas import JobOut
from app.models.job import JobStatus, JobType

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    user: CurrentUserDep,
    job_service: JobServiceDep,
) -> object:
    return await job_service.get_job(job_id, user.id)


@router.get("", response_model=list[JobOut])
async def list_jobs(
    user: CurrentUserDep,
    job_service: JobServiceDep,
    type: JobType | None = Query(default=None),
    status: JobStatus | None = Query(default=None),
) -> object:
    return await job_service.list_jobs(user.id, type=type, status=status)
