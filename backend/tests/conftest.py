"""Shared fixtures available to all test layers (unit, integration, e2e)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models import EMBEDDING_DIM, User, UserRole

# Re-export for use by all test modules
__all__ = ["_make_orm"]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def embedding_dim() -> int:
    return EMBEDDING_DIM


# ---------------------------------------------------------------------------
# Fake Settings
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def fake_settings():
    """A minimal Settings-like object for unit tests.

    Using a plain object avoids triggering pydantic-settings env-var
    resolution, which requires DATABASE_URL and JWT_SECRET to be set.
    """

    class _FakeSettings:
        database_url: str = "postgresql+asyncpg://test:test@localhost:5433/test"
        jwt_secret: str = "test-secret-key-for-tests-only"
        jwt_algorithm: str = "HS256"
        jwt_expires_minutes: int = 60
        redis_url: str = "redis://localhost:6379/0"
        ollama_host: str = "http://localhost:11434"
        ollama_chat_model: str = "test-chat-model"
        ollama_extract_model: str = ""
        ollama_embed_model: str = "test-embed-model"
        ollama_embed_dim: int = EMBEDDING_DIM
        llm_chat_provider: str = "ollama"
        llm_embed_provider: str = "ollama"
        cors_origins: str = "http://localhost:5173"

        @property
        def effective_extract_model(self) -> str:
            return self.ollama_extract_model.strip() or self.ollama_chat_model

        @property
        def cors_origin_list(self) -> list[str]:
            return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    return _FakeSettings()


# ---------------------------------------------------------------------------
# Mock LLM clients
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_llm_chat() -> AsyncMock:
    """AsyncMock satisfying LLMPort for chat calls."""
    mock = AsyncMock()
    mock.chat.return_value = {
        "message": {
            "role": "assistant",
            "content": "Hello!",
            "tool_calls": [],
        }
    }
    mock.embed.return_value = [0.1] * EMBEDDING_DIM
    mock.aclose.return_value = None
    return mock


@pytest.fixture
def mock_llm_embed() -> AsyncMock:
    """AsyncMock satisfying LLMPort for embed calls."""
    mock = AsyncMock()
    mock.embed.return_value = [0.1] * EMBEDDING_DIM
    mock.aclose.return_value = None
    return mock


# ---------------------------------------------------------------------------
# Fake user fixtures
# ---------------------------------------------------------------------------


def _make_orm(_cls=None, **kwargs):
    """Create a lightweight fake that behaves like a SQLAlchemy ORM instance.

    Uses SimpleNamespace so attribute access does not trigger SQLAlchemy
    descriptor instrumentation (which requires a live Session / mapper).
    The _cls argument is accepted for readability but not used structurally.
    """
    return SimpleNamespace(**kwargs)


def _make_user(
    user_id: int,
    email: str,
    role: UserRole,
) -> SimpleNamespace:
    """Create an in-memory User-like object (not persisted to any DB)."""
    return _make_orm(
        User,
        id=user_id,
        email=email,
        role=role,
        password_hash="fake-bcrypt-hash",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def fake_user() -> User:
    return _make_user(1, "student@test.com", UserRole.student)


@pytest.fixture
def fake_admin() -> User:
    return _make_user(2, "admin@test.com", UserRole.admin)
