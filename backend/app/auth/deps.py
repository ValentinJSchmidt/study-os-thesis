from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_core.security import decode_access_token
from app.auth.service import AuthService
from app.config import Settings, get_settings
from app.db import SessionLocal
from app.exceptions import ForbiddenException, UnauthorizedException
from app.llm.port import LLMPort
from app.models import User, UserRole
from app.users.repository import UserRepository

# ---------------------------------------------------------------------------
# Core: settings & DB session
# ---------------------------------------------------------------------------

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]

# ---------------------------------------------------------------------------
# Shared LLM clients
# ---------------------------------------------------------------------------


def get_llm_chat_client(request: Request) -> LLMPort:
    """Return the shared chat LLM client, or raise 503 if the provider is unavailable."""
    if not getattr(request.app.state, "llm_available", True):
        raise HTTPException(status_code=503, detail="LLM provider not reachable")
    return request.app.state.llm_chat_client


def get_llm_embed_client(request: Request) -> LLMPort:
    """Return the shared embed LLM client, or raise 503 if the provider is unavailable."""
    if not getattr(request.app.state, "llm_available", True):
        raise HTTPException(status_code=503, detail="LLM provider not reachable")
    return request.app.state.llm_embed_client


LLMChatClientDep = Annotated[LLMPort, Depends(get_llm_chat_client)]
LLMEmbedClientDep = Annotated[LLMPort, Depends(get_llm_embed_client)]

# ---------------------------------------------------------------------------
# User repository
# ---------------------------------------------------------------------------


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]

# ---------------------------------------------------------------------------
# Auth service
# ---------------------------------------------------------------------------


def get_auth_service(user_repo: UserRepoDep, settings: SettingsDep) -> AuthService:
    return AuthService(user_repo, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

# ---------------------------------------------------------------------------
# Authentication: current user & role guard
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """Decode the JWT and load the user via AuthService."""
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid token")
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid token subject")
    return await auth_service.get_user_by_id(user_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Factory that returns a dependency checking the user's role."""

    async def _checker(user: CurrentUserDep) -> User:
        if user.role not in roles:
            raise ForbiddenException(f"Requires role in {[r.value for r in roles]}")
        return user

    return _checker
