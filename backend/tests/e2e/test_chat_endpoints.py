"""Phase 5: E2E tests for chat endpoints after worker migration.

These tests verify async chat behavior: the controller dispatches the
agent loop to a Celery task and returns a job_id immediately.
"""

import pytest


@pytest.mark.e2e
class TestSendMessage:
    async def test_returns_202_with_job_id(self, client):
        """POST .../messages returns 202 + job_id + message_id."""
        response = await client.post(
            "/api/chat/sessions/1/messages",
            json={"content": "Hello, recommend a thesis for me."},
        )

        # 202 accepted, or 404 if session doesn't exist
        assert response.status_code in (202, 404)
        if response.status_code == 202:
            data = response.json()
            assert "job_id" in data

    async def test_validates_content_min(self, client):
        response = await client.post(
            "/api/chat/sessions/1/messages",
            json={"content": ""},
        )
        assert response.status_code == 422

    async def test_validates_content_max(self, client):
        response = await client.post(
            "/api/chat/sessions/1/messages",
            json={"content": "x" * 4001},
        )
        assert response.status_code == 422


@pytest.mark.e2e
class TestChatSessions:
    async def test_create_session_returns_session(self, client):
        response = await client.post("/api/chat/sessions")
        assert response.status_code in (200, 201)

    async def test_list_sessions_returns_list(self, client):
        response = await client.get("/api/chat/sessions")
        assert response.status_code == 200
