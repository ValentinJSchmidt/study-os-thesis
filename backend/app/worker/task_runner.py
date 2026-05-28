"""Shared lifecycle wrapper for Celery tasks.

Centralises the job-status transitions, WebSocket event publishing, and the
retry / dead-letter policy so every task behaves identically. A task body just
provides the actual unit of work as an async callable.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

from celery.exceptions import MaxRetriesExceededError

from app.exceptions import NotFoundException
from app.worker.job_status import mark_failure, mark_retry, mark_started, mark_success
from app.worker.publisher import publish_event
from app.worker.utils import run_async

logger = logging.getLogger(__name__)

_RETRYABLE: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError, OSError)
_PERMANENT: tuple[type[BaseException], ...] = (NotFoundException,)


def execute_task(
    task: Any,
    *,
    job_id: str,
    user_id: int,
    redis_url: str,
    work: Callable[[], Awaitable[dict]],
    success_event: str = "task_complete",
    started_event: str | None = None,
    started_data: dict | None = None,
    permanent_exceptions: tuple[type[BaseException], ...] = _PERMANENT,
    retryable_exceptions: tuple[type[BaseException], ...] = _RETRYABLE,
) -> dict:
    """Run ``work`` with full job-lifecycle bookkeeping.

    Transitions the job row pending -> started -> success/failure/retry, mirrors
    each transition onto the ``job_events`` Redis channel, and applies the retry
    policy. On exhausted retries the job is marked ``failure`` (dead letter).
    """
    mark_started(job_id)
    if started_event is not None:
        publish_event(
            redis_url,
            event_type=started_event,
            job_id=job_id,
            user_id=user_id,
            status="started",
            data=started_data or {},
        )

    try:
        result = run_async(work())
    except permanent_exceptions as exc:
        _fail(redis_url, job_id, user_id, str(exc))
        raise
    except retryable_exceptions as exc:
        mark_retry(job_id)
        publish_event(
            redis_url,
            event_type="task_failed",
            job_id=job_id,
            user_id=user_id,
            status="retry",
            data={"error": str(exc)},
        )
        try:
            raise task.retry(exc=exc)
        except MaxRetriesExceededError:
            _fail(redis_url, job_id, user_id, f"Exhausted retries: {exc}")
            raise
    except Exception:
        _fail(redis_url, job_id, user_id, traceback.format_exc()[:1000])
        raise

    mark_success(job_id, result)
    publish_event(
        redis_url,
        event_type=success_event,
        job_id=job_id,
        user_id=user_id,
        status="success",
        data=result,
    )
    return result


def _fail(redis_url: str, job_id: str, user_id: int, error: str) -> None:
    mark_failure(job_id, error)
    publish_event(
        redis_url,
        event_type="task_failed",
        job_id=job_id,
        user_id=user_id,
        status="failure",
        data={"error": error[:500]},
    )
