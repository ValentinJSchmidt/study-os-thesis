"""Redis Pub/Sub event publisher for Celery workers."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis as sync_redis

logger = logging.getLogger(__name__)


def publish_event(
    redis_url: str,
    *,
    event_type: str,
    job_id: str,
    user_id: int,
    status: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish an event to the ``job_events`` Redis Pub/Sub channel.

    Called from within Celery tasks to notify the API layer (and connected
    WebSocket clients) about job progress and completion.
    """
    payload = {
        "type": event_type,
        "job_id": job_id,
        "user_id": user_id,
        "status": status,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        r = sync_redis.from_url(redis_url)
        r.publish("job_events", json.dumps(payload))
    except Exception:
        logger.exception("Failed to publish event to Redis")
