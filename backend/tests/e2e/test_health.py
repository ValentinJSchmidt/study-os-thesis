"""E2E test for the health endpoint."""

import pytest


@pytest.mark.e2e
class TestHealth:
    async def test_health_returns_ok(self, client):
        response = await client.get("/api/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
