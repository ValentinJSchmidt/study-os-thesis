"""Utility helpers for running async code inside sync Celery tasks."""

import asyncio
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from a sync Celery task.

    Each call creates a fresh event loop via ``asyncio.run()``.
    This is safe because Celery prefork workers are separate processes
    with no pre-existing event loop.
    """
    return asyncio.run(coro)
