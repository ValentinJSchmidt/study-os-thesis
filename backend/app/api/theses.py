from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, require_role
from app.db import get_session
from app.llm.embeddings import embed_text
from app.models import Thesis, ThesisSource, User, UserRole
from app.schemas.thesis import ThesisCreate, ThesisOut

router = APIRouter(prefix="/api/theses", tags=["theses"])


@router.post("", response_model=ThesisOut, status_code=status.HTTP_201_CREATED)
async def create_thesis(
    body: ThesisCreate,
    user: Annotated[User, Depends(require_role(UserRole.professor, UserRole.student, UserRole.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Thesis:
    if body.supervisor_id is not None:
        supervisor = await session.get(User, body.supervisor_id)
        if not supervisor or supervisor.role != UserRole.professor:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "supervisor_id must reference a professor")

    source = ThesisSource.professor if user.role == UserRole.professor else ThesisSource.student

    embedding = await embed_text(f"{body.title}\n\n{body.abstract}")

    thesis = Thesis(
        title=body.title,
        abstract=body.abstract,
        supervisor_id=body.supervisor_id,
        submitter_id=user.id,
        source=source,
        embedding=embedding,
    )
    session.add(thesis)
    await session.commit()
    await session.refresh(thesis)
    return thesis


@router.get("", response_model=list[ThesisOut])
async def list_theses(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[Thesis]:
    rows = await session.scalars(
        select(Thesis).order_by(Thesis.created_at.desc()).limit(limit).offset(offset)
    )
    return list(rows)


@router.get("/{thesis_id}", response_model=ThesisOut)
async def get_thesis(
    thesis_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> Thesis:
    thesis = await session.get(Thesis, thesis_id)
    if not thesis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thesis not found")
    return thesis
