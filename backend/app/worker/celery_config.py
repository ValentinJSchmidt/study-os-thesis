"""Celery configuration for study-os-thesis workers."""

import os

broker_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Serialization
task_serializer: str = "json"
result_serializer: str = "json"
accept_content: list[str] = ["json"]

# Time
timezone: str = "UTC"
enable_utc: bool = True

# Task behaviour
task_track_started: bool = True
task_acks_late: bool = True
worker_prefetch_multiplier: int = 1
task_reject_on_worker_lost: bool = True

# Results
result_expires: int = 86400  # 24 hours
result_extended: bool = True

# Redis transport
broker_transport_options: dict = {
    "visibility_timeout": 3600,
}

# Concurrency
worker_concurrency: int = 4
