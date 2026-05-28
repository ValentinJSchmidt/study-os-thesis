"""Phase 6: Tests for retry policies and timeout configuration.

These tests verify the Celery task decorator settings.
They will FAIL until the task modules are implemented.
"""

import pytest


@pytest.mark.unit
class TestRetryPolicy:
    def test_embed_thesis_max_retries(self):
        from app.theses.tasks import embed_thesis

        assert embed_thesis.max_retries == 3

    def test_ingest_arxiv_max_retries(self):
        from app.chairs.tasks import ingest_arxiv_paper

        assert ingest_arxiv_paper.max_retries == 3

    def test_parse_transcript_max_retries(self):
        from app.students.tasks import parse_transcript

        assert parse_transcript.max_retries == 3

    def test_chat_turn_max_retries(self):
        from app.chat.tasks import process_chat_turn

        assert process_chat_turn.max_retries == 2


@pytest.mark.unit
class TestTimeoutConfig:
    def test_embed_thesis_soft_time_limit(self):
        from app.theses.tasks import embed_thesis

        assert embed_thesis.soft_time_limit == 120

    def test_embed_thesis_hard_time_limit(self):
        from app.theses.tasks import embed_thesis

        assert embed_thesis.time_limit == 180

    def test_parse_transcript_soft_time_limit(self):
        from app.students.tasks import parse_transcript

        assert parse_transcript.soft_time_limit == 300

    def test_parse_transcript_hard_time_limit(self):
        from app.students.tasks import parse_transcript

        assert parse_transcript.time_limit == 360

    def test_chat_turn_soft_time_limit(self):
        from app.chat.tasks import process_chat_turn

        assert process_chat_turn.soft_time_limit == 600

    def test_chat_turn_hard_time_limit(self):
        from app.chat.tasks import process_chat_turn

        assert process_chat_turn.time_limit == 660
