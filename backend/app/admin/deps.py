from typing import Annotated

from fastapi import Depends

from app.admin.service import AdminService
from app.auth.deps import UserRepoDep


def get_admin_service(user_repo: UserRepoDep) -> AdminService:
    return AdminService(user_repo)


AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
