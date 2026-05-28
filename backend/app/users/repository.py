from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole


class UserRepository:
    """Data-access layer for the `users` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def create(self, email: str, password_hash: str, role: UserRole) -> User:
        user = User(email=email, password_hash=password_hash, role=role)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def commit(self) -> None:
        await self._session.commit()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        rows = await self._session.scalars(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return list(rows)
