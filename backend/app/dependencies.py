"""Central dependency-injection providers for FastAPI.

Every repository, service, and shared client is wired here so that:
- route handlers receive thin, ready-to-use service objects,
- all dependencies are easily mockable in tests via ``app.dependency_overrides``.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.config import Settings, get_settings
from app.db import SessionLocal
from app.exceptions import ForbiddenException, UnauthorizedException
from app.llm.ollama_client import OllamaClient
from app.models import User, UserRole
from app.repositories.chair_repository import ChairRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.thesis_repository import ThesisRepository
from app.repositories.user_repository import UserRepository
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.chair_service import ChairService
from app.services.chat_service import ChatService
from app.services.student_service import StudentService
from app.services.thesis_service import ThesisService

# ---------------------------------------------------------------------------
# Core: settings & DB session
# ---------------------------------------------------------------------------

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]

# ---------------------------------------------------------------------------
# Shared clients
# ---------------------------------------------------------------------------


def get_ollama_client(request: Request) -> OllamaClient:
    """Return the single shared OllamaClient stored on app.state at startup."""
    return request.app.state.ollama_client


OllamaClientDep = Annotated[OllamaClient, Depends(get_ollama_client)]

# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_thesis_repository(session: SessionDep) -> ThesisRepository:
    return ThesisRepository(session)


def get_chat_repository(session: SessionDep) -> ChatRepository:
    return ChatRepository(session)


def get_student_repository(session: SessionDep) -> StudentRepository:
    return StudentRepository(session)


def get_chair_repository(session: SessionDep) -> ChairRepository:
    return ChairRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
ThesisRepoDep = Annotated[ThesisRepository, Depends(get_thesis_repository)]
ChatRepoDep = Annotated[ChatRepository, Depends(get_chat_repository)]
StudentRepoDep = Annotated[StudentRepository, Depends(get_student_repository)]
ChairRepoDep = Annotated[ChairRepository, Depends(get_chair_repository)]

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def get_auth_service(user_repo: UserRepoDep, settings: SettingsDep) -> AuthService:
    return AuthService(user_repo, settings)


def get_thesis_service(
    thesis_repo: ThesisRepoDep,
    user_repo: UserRepoDep,
    ollama: OllamaClientDep,
    settings: SettingsDep,
) -> ThesisService:
    return ThesisService(thesis_repo, user_repo, ollama, settings)


def get_chat_service(
    chat_repo: ChatRepoDep,
    ollama: OllamaClientDep,
    settings: SettingsDep,
    student_repo: StudentRepoDep,
    chair_repo: ChairRepoDep,
    thesis_repo: ThesisRepoDep,
) -> ChatService:
    return ChatService(
        chat_repo, ollama, settings,
        student_repo=student_repo,
        chair_repo=chair_repo,
        thesis_repo=thesis_repo,
    )


def get_admin_service(user_repo: UserRepoDep) -> AdminService:
    return AdminService(user_repo)


def get_student_service(
    student_repo: StudentRepoDep,
    ollama: OllamaClientDep,
    settings: SettingsDep,
) -> StudentService:
    return StudentService(student_repo, ollama, settings)


def get_chair_service(
    chair_repo: ChairRepoDep,
    ollama: OllamaClientDep,
    settings: SettingsDep,
) -> ChairService:
    return ChairService(chair_repo, ollama, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ThesisServiceDep = Annotated[ThesisService, Depends(get_thesis_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]
ChairServiceDep = Annotated[ChairService, Depends(get_chair_service)]

# ---------------------------------------------------------------------------
# Authentication dependencies
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


def require_role(*roles: UserRole):
    """Factory that returns a dependency checking the user's role."""

    async def _checker(user: CurrentUserDep) -> User:
        if user.role not in roles:
            raise ForbiddenException(
                f"Requires role in {[r.value for r in roles]}"
            )
        return user

    return _checker
