"""Phase 3: E2E tests for WebSocket endpoints."""

import pytest
from starlette.testclient import TestClient


@pytest.mark.e2e
class TestWebSocket:
    def test_websocket_requires_auth(self, _app):
        """Connecting without a token receives an error payload then is closed."""
        with TestClient(_app) as client:
            with client.websocket_connect("/api/ws") as ws:
                data = ws.receive_json()
                assert data["error"] == "Missing token"

    def test_websocket_rejects_invalid_token(self, _app):
        """Connecting with an invalid JWT receives an error payload then is closed."""
        with TestClient(_app) as client:
            with client.websocket_connect("/api/ws?token=invalid-jwt") as ws:
                data = ws.receive_json()
                assert data["error"] == "Invalid token"
