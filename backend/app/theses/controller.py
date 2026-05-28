from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth.deps import CurrentUserDep, require_role
from app.models import Thesis, User, UserRole
from app.theses.deps import ThesisServiceDep
from app.theses.schemas import ThesisCreate, ThesisOut

router = APIRouter(prefix="/api/theses", tags=["theses"])


@router.post("", response_model=ThesisOut, status_code=status.HTTP_201_CREATED)
async def create_thesis(
    body: ThesisCreate,
    user: Annotated[User, Depends(require_role(UserRole.professor, UserRole.admin))],
    thesis_service: ThesisServiceDep,
) -> Thesis:
    return await thesis_service.create_thesis(body, user)


@router.get("", response_model=list[ThesisOut])
async def list_theses(
    _user: CurrentUserDep,
    thesis_service: ThesisServiceDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[Thesis]:
    return await thesis_service.list_theses(limit=limit, offset=offset)


@router.get("/{thesis_id}", response_model=ThesisOut)
async def get_thesis(
    thesis_id: int,
    _user: CurrentUserDep,
    thesis_service: ThesisServiceDep,
) -> Thesis:
    return await thesis_service.get_thesis(thesis_id)
