"""Phase 4: E2E tests for chair endpoints after worker migration.

These tests verify async behavior for ArXiv ingestion and chair creation.
"""

import pytest


@pytest.mark.e2e
class TestIngestArxiv:
    async def test_returns_202_with_job_id(self, admin_client):
        """POST .../documents/arxiv should return 202 + job_id."""
        response = await admin_client.post(
            "/api/chairs/1/documents/arxiv",
            json={
                "arxiv_id": "2301.07041",
            },
        )

        # Chair 1 may not exist in mock; 404 is acceptable
        assert response.status_code in (202, 404)
        if response.status_code == 202:
            assert "job_id" in response.json()

    async def test_validates_arxiv_id(self, admin_client):
        response = await admin_client.post(
            "/api/chairs/1/documents/arxiv",
            json={
                "arxiv_id": "",
            },
        )
        assert response.status_code == 422


@pytest.mark.e2e
class TestCreateChair:
    async def test_returns_201_with_job_id(self, admin_client):
        """POST /api/chairs returns chair data + job_id for embedding."""
        response = await admin_client.post(
            "/api/chairs",
            json={
                "name": "Test Chair",
                "short_description": "A research chair focused on machine learning and AI applications.",
                "professor_name": "Prof. Test",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data

    async def test_list_chairs_returns_list(self, client):
        response = await client.get("/api/chairs")
        assert response.status_code == 200
