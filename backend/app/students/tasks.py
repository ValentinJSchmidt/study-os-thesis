"""Celery tasks for student-related background work."""

from __future__ import annotations

import logging
from typing import Any

from app.exceptions import BadRequestException, NotFoundException
from app.worker.celery_app import celery_app
from app.worker.task_runner import execute_task

logger = logging.getLogger(__name__)


async def _parse_transcript_work(
    user_id: int,
    job_id: str,
    settings: Any,
    program: str | None,
    semester: int | None,
) -> dict:
    from app.db import SessionLocal
    from app.llm.factory import build_chat_client, build_embed_client
    from app.students.pdf_store import delete_pdf, fetch_pdf
    from app.students.repository import StudentRepository
    from app.students.service import StudentService

    pdf_bytes = await fetch_pdf(settings.redis_url, job_id)
    if not pdf_bytes:
        raise BadRequestException("Transcript PDF was not found in temporary storage (it may have expired).")

    async with SessionLocal() as session:
        repo = StudentRepository(session)
        chat_client = build_chat_client(settings)
        embed_client = build_embed_client(settings)
        svc = StudentService(repo, chat_client, embed_client, settings)
        student = await svc.upload_transcript(user_id, pdf_bytes, program=program, semester=semester)

    await delete_pdf(settings.redis_url, job_id)
    return {
        "user_id": user_id,
        "courses": len(student.courses) if student.courses else 0,
    }


@celery_app.task(
    bind=True,
    name="app.students.tasks.parse_transcript",
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=360,
)
def parse_transcript(
    self: Any,
    user_id: int,
    job_id: str,
    program: str | None = None,
    semester: int | None = None,
) -> dict:
    """Parse a transcript PDF, extract courses via LLM, compute GPA, embed profile."""
    from app.config import get_settings

    settings = get_settings()
    logger.info("parse_transcript: user_id=%d job_id=%s", user_id, job_id)

    return execute_task(
        self,
        job_id=job_id,
        user_id=user_id,
        redis_url=settings.redis_url,
        work=lambda: _parse_transcript_work(user_id, job_id, settings, program, semester),
        permanent_exceptions=(NotFoundException, BadRequestException),
    )
