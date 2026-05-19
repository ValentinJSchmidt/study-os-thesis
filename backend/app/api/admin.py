from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import AdminServiceDep, require_role
from app.models import User, UserRole
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin: Annotated[User, Depends(require_role(UserRole.admin))],
    admin_service: AdminServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[User]:
    return await admin_service.list_users(limit=limit, offset=offset)
