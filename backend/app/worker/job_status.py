"""Job-table status updates for use inside sync Celery tasks.

Each helper runs in its own event loop and DB session via ``run_async`` so it is
self-contained: no ORM object or connection crosses event loops. Failures to
update the auxiliary jobs table are logged and swallowed so they never mask the
task's real outcome.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from app.worker.utils import run_async

logger = logging.getLogger(__name__)


async def _with_job_service(job_id: str, fn: Callable[[Any, uuid.UUID], Awaitable[Any]]) -> None:
    from app.db import SessionLocal
    from app.jobs.repository import JobRepository
    from app.jobs.service import JobService

    async with SessionLocal() as session:
        service = JobService(JobRepository(session))
        await fn(service, uuid.UUID(job_id))


def _run(job_id: str, fn: Callable[[Any, uuid.UUID], Awaitable[Any]]) -> None:
    try:
        run_async(_with_job_service(job_id, fn))
    except Exception:
        logger.exception("Failed to update job status for job_id=%s", job_id)


def mark_started(job_id: str) -> None:
    _run(job_id, lambda svc, jid: svc.mark_started(jid))


def mark_success(job_id: str, result_data: dict | None = None) -> None:
    _run(job_id, lambda svc, jid: svc.mark_success(jid, result_data=result_data))


def mark_failure(job_id: str, error: str) -> None:
    _run(job_id, lambda svc, jid: svc.mark_failure(jid, error=error))


def mark_retry(job_id: str) -> None:
    _run(job_id, lambda svc, jid: svc.mark_retry(jid))
