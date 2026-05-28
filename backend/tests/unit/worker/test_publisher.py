"""Phase 3: Tests for the Redis Pub/Sub event publisher.

These tests will FAIL until app.worker.publisher is implemented.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestPublishEvent:
    def test_publishes_to_job_events_channel(self):
        from app.worker.publisher import publish_event

        with patch("app.worker.publisher.sync_redis") as mock_redis_mod:
            mock_conn = MagicMock()
            mock_redis_mod.from_url.return_value = mock_conn

            publish_event(
                "redis://localhost:6379/0",
                event_type="task_complete",
                job_id="abc-123",
                user_id=1,
                status="success",
            )

            mock_conn.publish.assert_called_once()
            channel = mock_conn.publish.call_args[0][0]
            assert channel == "job_events"

    def test_payload_is_valid_json(self):
        from app.worker.publisher import publish_event

        with patch("app.worker.publisher.sync_redis") as mock_redis_mod:
            mock_conn = MagicMock()
            mock_redis_mod.from_url.return_value = mock_conn

            publish_event(
                "redis://localhost:6379/0",
                event_type="task_complete",
                job_id="abc-123",
                user_id=1,
                status="success",
            )

            raw = mock_conn.publish.call_args[0][1]
            data = json.loads(raw)
            assert data["type"] == "task_complete"
            assert data["job_id"] == "abc-123"
            assert data["user_id"] == 1
            assert data["status"] == "success"

    def test_payload_includes_iso_timestamp(self):
        from app.worker.publisher import publish_event
        from datetime import datetime

        with patch("app.worker.publisher.sync_redis") as mock_redis_mod:
            mock_conn = MagicMock()
            mock_redis_mod.from_url.return_value = mock_conn

            publish_event(
                "redis://localhost:6379/0",
                event_type="test",
                job_id="x",
                user_id=1,
                status="success",
            )

            raw = mock_conn.publish.call_args[0][1]
            data = json.loads(raw)
            # Should not raise
            datetime.fromisoformat(data["timestamp"])

    def test_payload_includes_data_dict(self):
        from app.worker.publisher import publish_event

        with patch("app.worker.publisher.sync_redis") as mock_redis_mod:
            mock_conn = MagicMock()
            mock_redis_mod.from_url.return_value = mock_conn

            publish_event(
                "redis://localhost:6379/0",
                event_type="test",
                job_id="x",
                user_id=1,
                status="success",
                data={"thesis_id": 42},
            )

            raw = mock_conn.publish.call_args[0][1]
            data = json.loads(raw)
            assert data["data"] == {"thesis_id": 42}

    def test_redis_error_does_not_raise(self):
        from app.worker.publisher import publish_event

        with patch("app.worker.publisher.sync_redis") as mock_redis_mod:
            mock_redis_mod.from_url.side_effect = ConnectionError("Redis down")

            # Should not raise
            publish_event(
                "redis://localhost:6379/0",
                event_type="test",
                job_id="x",
                user_id=1,
                status="success",
            )
