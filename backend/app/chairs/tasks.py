"""Celery tasks for chair-related background work."""

from __future__ import annotations

import logging
from typing import Any

from app.exceptions import AlreadyExistsException, NotFoundException
from app.worker.celery_app import celery_app
from app.worker.task_runner import execute_task

logger = logging.getLogger(__name__)


async def _ingest_arxiv_work(chair_id: int, arxiv_id: str, settings: Any) -> dict:
    from app.chairs.repository import ChairRepository
    from app.chairs.schemas import ArxivIngestRequest
    from app.chairs.service import ChairService
    from app.db import SessionLocal
    from app.llm.factory import build_embed_client

    async with SessionLocal() as session:
        repo = ChairRepository(session)
        embed_client = build_embed_client(settings)
        svc = ChairService(repo, embed_client, settings)
        doc = await svc.ingest_arxiv_paper(chair_id, ArxivIngestRequest(arxiv_id=arxiv_id))
        return {"document_id": doc.id, "title": doc.title}


async def _embed_chair_work(chair_id: int, settings: Any) -> dict:
    from app.chairs.repository import ChairRepository
    from app.db import SessionLocal
    from app.llm.factory import build_embed_client
    from app.models.chair import ChairDocumentKind

    async with SessionLocal() as session:
        repo = ChairRepository(session)
        chair = await repo.get_by_id(chair_id)
        if chair is None:
            raise NotFoundException("Chair", chair_id)
        embed_client = build_embed_client(settings)
        try:
            embedding = await embed_client.embed(settings.ollama_embed_model, chair.short_description)
        except Exception:
            embedding = None
        await repo.add_document(
            chair_id=chair_id,
            kind=ChairDocumentKind.description,
            content=chair.short_description,
            embedding=embedding,
        )
        await repo.commit()
        return {"chair_id": chair_id}


@celery_app.task(
    bind=True,
    name="app.chairs.tasks.ingest_arxiv_paper",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=180,
)
def ingest_arxiv_paper(self: Any, chair_id: int, arxiv_id: str, user_id: int, job_id: str) -> dict:
    """Fetch an ArXiv paper, embed its abstract, and store it."""
    from app.config import get_settings

    settings = get_settings()
    logger.info("ingest_arxiv_paper: chair_id=%d arxiv_id=%s job_id=%s", chair_id, arxiv_id, job_id)

    return execute_task(
        self,
        job_id=job_id,
        user_id=user_id,
        redis_url=settings.redis_url,
        work=lambda: _ingest_arxiv_work(chair_id, arxiv_id, settings),
        permanent_exceptions=(NotFoundException, AlreadyExistsException),
    )


@celery_app.task(
    bind=True,
    name="app.chairs.tasks.embed_chair_description",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=180,
)
def embed_chair_description(self: Any, chair_id: int, user_id: int, job_id: str) -> dict:
    """Embed a chair's description and store it as a ChairDocument."""
    from app.config import get_settings

    settings = get_settings()
    logger.info("embed_chair_description: chair_id=%d job_id=%s", chair_id, job_id)

    return execute_task(
        self,
        job_id=job_id,
        user_id=user_id,
        redis_url=settings.redis_url,
        work=lambda: _embed_chair_work(chair_id, settings),
    )
