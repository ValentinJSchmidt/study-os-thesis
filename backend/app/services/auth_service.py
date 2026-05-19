from app.auth.security import create_access_token, hash_password, verify_password
from app.config import Settings
from app.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    InvalidCredentialsException,
    UnauthorizedException,
)
from app.models import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """Business logic for authentication and user registration."""

    def __init__(self, user_repo: UserRepository, settings: Settings) -> None:
        self._user_repo = user_repo
        self._settings = settings

    async def register(self, data: RegisterRequest) -> User:
        if data.role == UserRole.admin:
            raise BadRequestException("Admin cannot self-register")

        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise AlreadyExistsException("User", "email", data.email)

        hashed = await hash_password(data.password)
        user = await self._user_repo.create(
            email=data.email,
            password_hash=hashed,
            role=data.role,
        )
        await self._user_repo.commit()
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._user_repo.get_by_email(data.email)
        if not user or not await verify_password(data.password, user.password_hash):
            raise InvalidCredentialsException()

        token = create_access_token(
            sub=str(user.id),
            extra={"role": user.role.value},
        )
        return TokenResponse(access_token=token)

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")
        return user
