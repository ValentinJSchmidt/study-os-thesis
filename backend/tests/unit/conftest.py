"""Unit-test specific fixtures: mock repositories and services."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_thesis_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_chair_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_student_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_chat_repo() -> AsyncMock:
    return AsyncMock()
