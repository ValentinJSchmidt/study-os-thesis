from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db import get_session
from app.models import User, UserRole
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin: Annotated[User, Depends(require_role(UserRole.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[User]:
    rows = await session.scalars(select(User).order_by(User.created_at.desc()))
    return list(rows)
