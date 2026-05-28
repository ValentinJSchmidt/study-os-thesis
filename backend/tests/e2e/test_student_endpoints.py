"""Phase 4: E2E tests for student endpoints after worker migration."""

import pytest


@pytest.mark.e2e
class TestUploadTranscript:
    async def test_returns_202_with_job_id(self, client):
        """POST .../transcript returns 202 + job_id."""
        response = await client.post(
            "/api/students/me/transcript",
            files={"file": ("transcript.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            data={"program": "CS", "semester": "4"},
        )
        assert response.status_code == 202
        assert "job_id" in response.json()

    async def test_rejects_non_pdf(self, client):
        response = await client.post(
            "/api/students/me/transcript",
            files={"file": ("readme.txt", b"plain text", "text/plain")},
        )
        assert response.status_code == 400


@pytest.mark.e2e
class TestGetProfile:
    async def test_works_before_transcript(self, client):
        """GET /api/students/me should work even without a transcript."""
        response = await client.get("/api/students/me")
        # 200 if profile exists, 404 if not
        assert response.status_code in (200, 404)
