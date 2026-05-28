"""Lifecycle tests for the shared Celery task runner.

These assert the job-table transitions, WebSocket event publishing, and the
retry / dead-letter policy that every task relies on.
"""

from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import MaxRetriesExceededError, Retry

from app.exceptions import NotFoundException
from app.worker import task_runner


@pytest.fixture
def lifecycle_patches():
    with (
        patch.object(task_runner, "mark_started") as started,
        patch.object(task_runner, "mark_success") as success,
        patch.object(task_runner, "mark_failure") as failure,
        patch.object(task_runner, "mark_retry") as retry,
        patch.object(task_runner, "publish_event") as publish,
        patch.object(task_runner, "run_async") as run,
    ):
        yield {
            "started": started,
            "success": success,
            "failure": failure,
            "retry": retry,
            "publish": publish,
            "run": run,
        }


def _call(task=None, **overrides):
    kwargs = dict(
        job_id="job-1",
        user_id=7,
        redis_url="redis://x",
        work=lambda: "coro",
    )
    kwargs.update(overrides)
    return task_runner.execute_task(task or MagicMock(), **kwargs)


@pytest.mark.unit
class TestHappyPath:
    def test_marks_started_then_success(self, lifecycle_patches):
        lifecycle_patches["run"].return_value = {"ok": True}

        result = _call()

        assert result == {"ok": True}
        lifecycle_patches["started"].assert_called_once_with("job-1")
        lifecycle_patches["success"].assert_called_once_with("job-1", {"ok": True})
        lifecycle_patches["failure"].assert_not_called()

    def test_publishes_success_event(self, lifecycle_patches):
        lifecycle_patches["run"].return_value = {"dim": 3}

        _call(success_event="task_complete")

        kw = lifecycle_patches["publish"].call_args.kwargs
        assert kw["event_type"] == "task_complete"
        assert kw["status"] == "success"
        assert kw["data"] == {"dim": 3}

    def test_started_event_published_when_requested(self, lifecycle_patches):
        lifecycle_patches["run"].return_value = {}

        _call(started_event="chat_turn_started", started_data={"session_id": 5})

        events = [c.kwargs["event_type"] for c in lifecycle_patches["publish"].call_args_list]
        assert events[0] == "chat_turn_started"
        assert lifecycle_patches["publish"].call_args_list[0].kwargs["status"] == "started"

    def test_no_started_event_by_default(self, lifecycle_patches):
        lifecycle_patches["run"].return_value = {}

        _call()

        events = [c.kwargs["event_type"] for c in lifecycle_patches["publish"].call_args_list]
        assert "task_complete" in events
        assert all(e != "chat_turn_started" for e in events)


@pytest.mark.unit
class TestPermanentFailure:
    def test_not_found_marks_failure_no_retry(self, lifecycle_patches):
        task = MagicMock()
        lifecycle_patches["run"].side_effect = NotFoundException("Thesis", 1)

        with pytest.raises(NotFoundException):
            _call(task)

        lifecycle_patches["failure"].assert_called_once()
        lifecycle_patches["retry"].assert_not_called()
        task.retry.assert_not_called()
        kw = lifecycle_patches["publish"].call_args.kwargs
        assert kw["status"] == "failure"

    def test_generic_exception_marks_failure(self, lifecycle_patches):
        lifecycle_patches["run"].side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            _call()

        lifecycle_patches["failure"].assert_called_once()
        lifecycle_patches["success"].assert_not_called()

    def test_custom_permanent_exception(self, lifecycle_patches):
        class Dup(Exception):
            pass

        lifecycle_patches["run"].side_effect = Dup()

        with pytest.raises(Dup):
            _call(permanent_exceptions=(Dup,))

        lifecycle_patches["failure"].assert_called_once()
        lifecycle_patches["retry"].assert_not_called()


@pytest.mark.unit
class TestRetry:
    def test_connection_error_triggers_retry(self, lifecycle_patches):
        task = MagicMock()
        task.retry.side_effect = Retry()
        lifecycle_patches["run"].side_effect = ConnectionError("down")

        with pytest.raises(Retry):
            _call(task)

        lifecycle_patches["retry"].assert_called_once_with("job-1")
        task.retry.assert_called_once()
        # retry event published before the retry is raised
        statuses = [c.kwargs["status"] for c in lifecycle_patches["publish"].call_args_list]
        assert "retry" in statuses
        lifecycle_patches["failure"].assert_not_called()

    def test_exhausted_retries_marks_failure(self, lifecycle_patches):
        task = MagicMock()
        task.retry.side_effect = MaxRetriesExceededError()
        lifecycle_patches["run"].side_effect = TimeoutError("slow")

        with pytest.raises(MaxRetriesExceededError):
            _call(task)

        lifecycle_patches["retry"].assert_called_once()
        lifecycle_patches["failure"].assert_called_once()
        statuses = [c.kwargs["status"] for c in lifecycle_patches["publish"].call_args_list]
        assert "retry" in statuses
        assert "failure" in statuses
