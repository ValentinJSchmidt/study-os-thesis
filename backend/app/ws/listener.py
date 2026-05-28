"""Redis Pub/Sub → WebSocket bridge."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)


async def _handle_message(raw: dict[str, Any], manager: ConnectionManager) -> None:
    """Process a single Redis Pub/Sub message.

    Extracted as a standalone function for easy unit testing.
    """
    if raw.get("type") != "message":
        return

    data_bytes = raw.get("data")
    if data_bytes is None:
        return

    try:
        if isinstance(data_bytes, bytes):
            data = json.loads(data_bytes.decode())
        else:
            data = json.loads(data_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Malformed JSON in Redis Pub/Sub message")
        return

    user_id = data.get("user_id")
    if user_id is None:
        logger.debug("Redis event missing user_id, skipping")
        return

    await manager.send_to_user(user_id, data)


async def _aclose(pubsub: Any, client: Any) -> None:
    for closer in (pubsub, client):
        try:
            await closer.aclose()
        except Exception:
            pass


async def redis_listener(manager: ConnectionManager, redis_url: str, *, retry_delay: float = 5.0) -> None:
    """Subscribe to ``job_events`` and dispatch messages to WebSocket clients.

    Runs as an ``asyncio.Task`` in the FastAPI lifespan. Resilient to Redis being
    unavailable: connection failures are logged and retried with a fixed delay so
    a Redis outage (e.g. at startup) never crashes the app, and cancellation at
    shutdown is handled cleanly.
    """
    import redis.asyncio as aioredis

    while True:
        client = aioredis.from_url(redis_url)
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe("job_events")
            async for message in pubsub.listen():
                await _handle_message(message, manager)
        except asyncio.CancelledError:
            await _aclose(pubsub, client)
            raise
        except Exception:
            logger.warning("Redis listener error; reconnecting in %.0fs", retry_delay, exc_info=True)
            await _aclose(pubsub, client)
        else:
            await _aclose(pubsub, client)
        await asyncio.sleep(retry_delay)
