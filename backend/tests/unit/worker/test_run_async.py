"""Phase 1: Tests for the run_async utility.

These tests will FAIL until app.worker.utils is implemented.
"""

import pytest


@pytest.mark.unit
class TestRunAsync:
    def test_returns_coroutine_result(self):
        from app.worker.utils import run_async

        async def _coro():
            return 42

        assert run_async(_coro()) == 42

    def test_propagates_exception(self):
        from app.worker.utils import run_async

        async def _coro():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            run_async(_coro())

    def test_works_consecutively(self):
        from app.worker.utils import run_async

        async def _coro(n):
            return n

        assert run_async(_coro(1)) == 1
        assert run_async(_coro(2)) == 2
