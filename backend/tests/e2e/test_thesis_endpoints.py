"""Phase 4: E2E tests for thesis endpoints after worker migration.

These tests verify the new async behavior: the controller dispatches
embedding to a Celery task and returns a job_id immediately.
"""

import pytest


@pytest.mark.e2e
class TestCreateThesis:
    async def test_returns_201_with_job_id(self, admin_client):
        """POST /api/theses should return thesis data including a job_id."""
        response = await admin_client.post(
            "/api/theses",
            json={
                "title": "Test Thesis Title",
                "abstract": "A sufficiently long abstract for validation purposes.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data

    async def test_stores_thesis_without_embedding(self, admin_client):
        """Thesis is persisted immediately; embedding happens in worker."""
        response = await admin_client.post(
            "/api/theses",
            json={
                "title": "Another Thesis",
                "abstract": "Long enough abstract for the validation schema to accept.",
            },
        )

        assert response.status_code == 201

    async def test_dispatches_celery_task(self, admin_client):
        """Creating a thesis should dispatch an embed_thesis Celery task."""
        response = await admin_client.post(
            "/api/theses",
            json={
                "title": "Task Dispatch Test",
                "abstract": "A sufficiently long abstract for validation purposes.",
            },
        )

        assert response.status_code == 201

    async def test_dispatches_with_real_job_id(self, admin_client, _celery_patch):
        """The task must receive the real job id, not a 'pending' placeholder."""
        import uuid

        response = await admin_client.post(
            "/api/theses",
            json={
                "title": "Real Job Id Test",
                "abstract": "A sufficiently long abstract for validation purposes.",
            },
        )

        assert response.status_code == 201
        job_id = response.json()["job_id"]

        delay = _celery_patch["embed_thesis"]
        passed_job_id = delay.call_args.args[2]
        assert passed_job_id != "pending"
        uuid.UUID(passed_job_id)  # must be a valid UUID string
        assert passed_job_id == job_id

    async def test_validates_title_min_length(self, admin_client):
        response = await admin_client.post(
            "/api/theses",
            json={
                "title": "AB",
                "abstract": "A sufficiently long abstract for validation purposes.",
            },
        )
        assert response.status_code == 422

    async def test_requires_admin_role(self, client):
        """Student user should get 403."""
        response = await client.post(
            "/api/theses",
            json={
                "title": "Test Thesis",
                "abstract": "A sufficiently long abstract for validation purposes.",
            },
        )
        assert response.status_code == 403

    async def test_get_thesis_returns_list(self, client):
        """GET /api/theses should return a list."""
        response = await client.get("/api/theses")
        assert response.status_code == 200
