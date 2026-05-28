from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.admin.deps import AdminServiceDep
from app.auth.deps import require_role
from app.auth.schemas import UserOut
from app.models import User, UserRole

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin: Annotated[User, Depends(require_role(UserRole.admin))],
    admin_service: AdminServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[User]:
    return await admin_service.list_users(limit=limit, offset=offset)
