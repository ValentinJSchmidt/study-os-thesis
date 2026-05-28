from app.models import User
from app.users.repository import UserRepository


class AdminService:
    """Business logic for admin-only operations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def list_users(self, limit: int = 50, offset: int = 0) -> list[User]:
        return await self._user_repo.list_all(limit=limit, offset=offset)
