"""Phase 3: Tests for the WebSocket ConnectionManager.

These tests will FAIL until app.ws.manager is implemented.
"""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.unit
class TestConnectionManager:
    def _make_manager(self):
        from app.ws.manager import ConnectionManager

        return ConnectionManager()

    def _mock_ws(self):
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    async def test_connect_registers_websocket(self):
        manager = self._make_manager()
        ws = self._mock_ws()

        await manager.connect(user_id=1, ws=ws)

        # Verify the manager tracks it (implementation-specific check)
        assert manager._connections.get(1) is not None
        assert ws in manager._connections[1]

    async def test_disconnect_removes_websocket(self):
        manager = self._make_manager()
        ws = self._mock_ws()
        await manager.connect(user_id=1, ws=ws)

        manager.disconnect(user_id=1, ws=ws)

        assert ws not in manager._connections.get(1, [])

    async def test_disconnect_unknown_is_noop(self):
        manager = self._make_manager()
        ws = self._mock_ws()

        # Should not raise
        manager.disconnect(user_id=999, ws=ws)

    async def test_send_to_user_calls_send_json(self):
        manager = self._make_manager()
        ws = self._mock_ws()
        await manager.connect(user_id=1, ws=ws)

        await manager.send_to_user(1, {"type": "test"})

        ws.send_json.assert_called_once_with({"type": "test"})

    async def test_send_to_user_no_connections_is_noop(self):
        manager = self._make_manager()

        # Should not raise
        await manager.send_to_user(999, {"type": "test"})

    async def test_multiple_connections_per_user(self):
        manager = self._make_manager()
        ws1 = self._mock_ws()
        ws2 = self._mock_ws()
        await manager.connect(user_id=1, ws=ws1)
        await manager.connect(user_id=1, ws=ws2)

        await manager.send_to_user(1, {"type": "test"})

        ws1.send_json.assert_called_once_with({"type": "test"})
        ws2.send_json.assert_called_once_with({"type": "test"})

    async def test_stale_connection_does_not_crash(self):
        manager = self._make_manager()
        ws = self._mock_ws()
        ws.send_json.side_effect = RuntimeError("connection closed")
        await manager.connect(user_id=1, ws=ws)

        # Should not raise
        await manager.send_to_user(1, {"type": "test"})

    async def test_send_to_wrong_user_delivers_nothing(self):
        manager = self._make_manager()
        ws = self._mock_ws()
        await manager.connect(user_id=1, ws=ws)

        await manager.send_to_user(2, {"type": "test"})

        ws.send_json.assert_not_called()
