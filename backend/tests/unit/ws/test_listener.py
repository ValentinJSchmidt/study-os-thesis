"""Phase 3: Tests for the Redis Pub/Sub listener.

These tests will FAIL until app.ws.listener is implemented.
"""

import json
from unittest.mock import AsyncMock

import pytest


@pytest.mark.unit
class TestRedisListener:
    async def test_dispatches_message_to_manager(self):
        from app.ws.listener import _handle_message

        manager = AsyncMock()
        data = {"type": "task_complete", "job_id": "abc", "user_id": 1, "status": "success"}
        raw_message = {"type": "message", "data": json.dumps(data).encode()}

        await _handle_message(raw_message, manager)

        manager.send_to_user.assert_called_once_with(1, data)

    async def test_ignores_subscribe_messages(self):
        from app.ws.listener import _handle_message

        manager = AsyncMock()
        raw_message = {"type": "subscribe", "data": None}

        await _handle_message(raw_message, manager)

        manager.send_to_user.assert_not_called()

    async def test_handles_malformed_json(self):
        from app.ws.listener import _handle_message

        manager = AsyncMock()
        raw_message = {"type": "message", "data": b"not-json"}

        # Should not raise
        await _handle_message(raw_message, manager)

        manager.send_to_user.assert_not_called()

    async def test_handles_missing_user_id(self):
        from app.ws.listener import _handle_message

        manager = AsyncMock()
        data = {"type": "task_complete", "job_id": "abc"}  # no user_id
        raw_message = {"type": "message", "data": json.dumps(data).encode()}

        # Should not raise
        await _handle_message(raw_message, manager)

        manager.send_to_user.assert_not_called()
