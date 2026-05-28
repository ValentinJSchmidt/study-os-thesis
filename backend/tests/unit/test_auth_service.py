"""Unit tests for AuthService."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.auth.service import AuthService
from app.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    InvalidCredentialsException,
    UnauthorizedException,
)
from app.models import User, UserRole
from tests.conftest import _make_orm


@pytest.fixture
def auth_service(mock_user_repo, fake_settings) -> AuthService:
    return AuthService(mock_user_repo, fake_settings)


@pytest.mark.unit
class TestRegister:
    async def test_register_creates_user(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        fake_user = _make_orm(User, id=1, email="new@test.com", role=UserRole.student)
        mock_user_repo.create.return_value = fake_user

        with patch("app.auth.service.hash_password", new_callable=AsyncMock) as mock_hash:
            mock_hash.return_value = "hashed-pw"
            data = RegisterRequest(email="new@test.com", password="password123")
            result = await auth_service.register(data)

        mock_user_repo.create.assert_called_once()
        call_kwargs = mock_user_repo.create.call_args
        assert call_kwargs.kwargs["email"] == "new@test.com"
        assert call_kwargs.kwargs["password_hash"] == "hashed-pw"
        mock_user_repo.commit.assert_called_once()
        assert result.email == "new@test.com"

    async def test_register_hashes_password(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = _make_orm(User, id=1)

        with patch("app.auth.service.hash_password", new_callable=AsyncMock) as mock_hash:
            mock_hash.return_value = "bcrypt-hash"
            data = RegisterRequest(email="x@test.com", password="plaintext1")
            await auth_service.register(data)

        mock_user_repo.create.assert_called_once()
        assert mock_user_repo.create.call_args.kwargs["password_hash"] != "plaintext1"

    async def test_register_duplicate_email_raises(self, auth_service, mock_user_repo):
        existing = _make_orm(User, email="taken@test.com")
        mock_user_repo.get_by_email.return_value = existing

        with pytest.raises(AlreadyExistsException):
            data = RegisterRequest(email="taken@test.com", password="password123")
            await auth_service.register(data)

    async def test_register_admin_role_raises(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        with pytest.raises(BadRequestException, match="Admin cannot self-register"):
            data = RegisterRequest(email="a@test.com", password="password123", role=UserRole.admin)
            await auth_service.register(data)


@pytest.mark.unit
class TestLogin:
    async def test_login_valid_credentials_returns_token(self, auth_service, mock_user_repo):
        user = _make_orm(User, id=1, email="user@test.com", role=UserRole.student, password_hash="stored-hash")
        mock_user_repo.get_by_email.return_value = user

        with patch("app.auth.service.verify_password", new_callable=AsyncMock) as mock_verify, patch("app.auth.service.create_access_token") as mock_token:
            mock_verify.return_value = True
            mock_token.return_value = "jwt-token-123"
            data = LoginRequest(email="user@test.com", password="correct-pw")
            result = await auth_service.login(data)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "jwt-token-123"

    async def test_login_unknown_email_raises(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsException):
            data = LoginRequest(email="nobody@test.com", password="anything1")
            await auth_service.login(data)

    async def test_login_wrong_password_raises(self, auth_service, mock_user_repo):
        user = _make_orm(User, id=1, password_hash="stored-hash")
        mock_user_repo.get_by_email.return_value = user

        with patch("app.auth.service.verify_password", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = False
            with pytest.raises(InvalidCredentialsException):
                data = LoginRequest(email="user@test.com", password="wrong-pw1")
                await auth_service.login(data)


@pytest.mark.unit
class TestGetUserById:
    async def test_get_user_by_id_returns_user(self, auth_service, mock_user_repo):
        user = _make_orm(User, id=1)
        mock_user_repo.get_by_id.return_value = user

        result = await auth_service.get_user_by_id(1)
        assert result.id == 1
        mock_user_repo.get_by_id.assert_called_once_with(1)

    async def test_get_user_by_id_not_found_raises(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UnauthorizedException):
            await auth_service.get_user_by_id(999)
