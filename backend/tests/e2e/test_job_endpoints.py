"""Phase 2: E2E tests for job status endpoints."""

import uuid

import pytest

from app.exceptions import NotFoundException


@pytest.mark.e2e
class TestGetJob:
    async def test_get_job_200(self, client):
        """Mock returns a job, so we get 200."""
        response = await client.get(f"/api/jobs/{uuid.uuid4()}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data

    async def test_get_job_not_found_404(self, _app, client):
        """Override get_job to raise NotFoundException."""
        from app.jobs.deps import get_job_service
        from unittest.mock import AsyncMock

        mock_svc = AsyncMock()
        mock_svc.get_job.side_effect = NotFoundException("Job", "nonexistent")
        mock_svc.list_jobs.return_value = []
        _app.dependency_overrides[get_job_service] = lambda: mock_svc

        response = await client.get(f"/api/jobs/{uuid.uuid4()}")
        assert response.status_code == 404


@pytest.mark.e2e
class TestListJobs:
    async def test_list_jobs_returns_own_jobs(self, client):
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_jobs_filter_by_type(self, client):
        response = await client.get("/api/jobs?type=embed_thesis")
        assert response.status_code == 200

    async def test_list_jobs_filter_by_status(self, client):
        response = await client.get("/api/jobs?status=pending")
        assert response.status_code == 200
