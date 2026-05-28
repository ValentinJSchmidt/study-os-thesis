"""Celery tasks for thesis-related background work."""

from __future__ import annotations

import logging
from typing import Any

from app.exceptions import NotFoundException
from app.worker.celery_app import celery_app
from app.worker.task_runner import execute_task

logger = logging.getLogger(__name__)


async def _embed_thesis_work(thesis_id: int, settings: Any) -> dict:
    from app.db import SessionLocal
    from app.llm.factory import build_embed_client
    from app.theses.repository import ThesisRepository

    async with SessionLocal() as session:
        repo = ThesisRepository(session)
        thesis = await repo.get_by_id(thesis_id)
        if thesis is None:
            raise NotFoundException("Thesis", thesis_id)

        embed_client = build_embed_client(settings)
        embedding = await embed_client.embed(
            settings.ollama_embed_model,
            f"{thesis.title}\n\n{thesis.abstract}",
        )
        thesis.embedding = embedding
        await session.commit()
        return {"thesis_id": thesis_id, "dim": len(embedding)}


@celery_app.task(
    bind=True,
    name="app.theses.tasks.embed_thesis",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=180,
)
def embed_thesis(self: Any, thesis_id: int, user_id: int, job_id: str) -> dict:
    """Generate and store the embedding for a thesis."""
    from app.config import get_settings

    settings = get_settings()
    logger.info("embed_thesis: thesis_id=%d job_id=%s", thesis_id, job_id)

    return execute_task(
        self,
        job_id=job_id,
        user_id=user_id,
        redis_url=settings.redis_url,
        work=lambda: _embed_thesis_work(thesis_id, settings),
    )
