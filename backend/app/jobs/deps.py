"""Dependency injection wiring for the jobs domain."""

from typing import Annotated

from fastapi import Depends

from app.auth.deps import SessionDep
from app.jobs.repository import JobRepository
from app.jobs.service import JobService


def get_job_repository(session: SessionDep) -> JobRepository:
    return JobRepository(session)


JobRepoDep = Annotated[JobRepository, Depends(get_job_repository)]


def get_job_service(job_repo: JobRepoDep) -> JobService:
    return JobService(job_repo)


JobServiceDep = Annotated[JobService, Depends(get_job_service)]
