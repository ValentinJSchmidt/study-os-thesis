"""Temporary storage for uploaded transcript PDFs.

The HTTP request reads the PDF bytes, but the actual parsing happens later in a
Celery worker. We stash the bytes in Redis keyed by job id (with a TTL so they
cannot leak indefinitely) and the worker retrieves them.
"""

from __future__ import annotations

import redis.asyncio as aioredis

_PDF_TTL_SECONDS = 3600


def _key(job_id: str) -> str:
    return f"transcript_pdf:{job_id}"


async def store_pdf(redis_url: str, job_id: str, data: bytes) -> None:
    client = aioredis.from_url(redis_url)
    try:
        await client.set(_key(job_id), data, ex=_PDF_TTL_SECONDS)
    finally:
        await client.aclose()


async def fetch_pdf(redis_url: str, job_id: str) -> bytes | None:
    client = aioredis.from_url(redis_url)
    try:
        return await client.get(_key(job_id))
    finally:
        await client.aclose()


async def delete_pdf(redis_url: str, job_id: str) -> None:
    client = aioredis.from_url(redis_url)
    try:
        await client.delete(_key(job_id))
    finally:
        await client.aclose()
