"""Phase 1: Tests for Celery configuration.

These tests will FAIL until app.worker.celery_config is implemented.
"""

import pytest


@pytest.mark.unit
class TestCeleryConfig:
    def test_broker_url_uses_redis(self):
        from app.worker import celery_config

        assert celery_config.broker_url.startswith("redis://")

    def test_result_backend_uses_redis(self):
        from app.worker import celery_config

        assert celery_config.result_backend.startswith("redis://")

    def test_task_serializer_is_json(self):
        from app.worker import celery_config

        assert celery_config.task_serializer == "json"

    def test_result_serializer_is_json(self):
        from app.worker import celery_config

        assert celery_config.result_serializer == "json"

    def test_task_acks_late_enabled(self):
        from app.worker import celery_config

        assert celery_config.task_acks_late is True

    def test_task_track_started_enabled(self):
        from app.worker import celery_config

        assert celery_config.task_track_started is True

    def test_worker_prefetch_multiplier_is_one(self):
        from app.worker import celery_config

        assert celery_config.worker_prefetch_multiplier == 1

    def test_task_reject_on_worker_lost_enabled(self):
        from app.worker import celery_config

        assert celery_config.task_reject_on_worker_lost is True

    def test_result_expires_is_24h(self):
        from app.worker import celery_config

        assert celery_config.result_expires == 86400
