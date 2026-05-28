from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.deps import CurrentUserDep, require_role
from app.chairs.deps import ChairServiceDep
from app.chairs.schemas import ArxivIngestRequest, ChairCreate, ChairDocumentOut, ChairOut, ChairPatch
from app.models import User, UserRole

router = APIRouter(prefix="/api/chairs", tags=["chairs"])

AdminDep = Annotated[User, Depends(require_role(UserRole.admin))]


@router.get("", response_model=list[ChairOut])
async def list_chairs(
    _user: CurrentUserDep,
    chair_service: ChairServiceDep,
) -> list[ChairOut]:
    return await chair_service.list_chairs()


@router.get("/{chair_id}", response_model=ChairOut)
async def get_chair(
    chair_id: int,
    _user: CurrentUserDep,
    chair_service: ChairServiceDep,
) -> ChairOut:
    return await chair_service.get_chair(chair_id)


@router.post("", response_model=ChairOut, status_code=status.HTTP_201_CREATED)
async def create_chair(
    body: ChairCreate,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> ChairOut:
    return await chair_service.create_chair(body)


@router.patch("/{chair_id}", response_model=ChairOut)
async def update_chair(
    chair_id: int,
    body: ChairPatch,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> ChairOut:
    return await chair_service.update_chair(chair_id, body)


@router.delete("/{chair_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chair(
    chair_id: int,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> None:
    await chair_service.delete_chair(chair_id)


@router.post(
    "/{chair_id}/documents/arxiv",
    response_model=ChairDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_arxiv_paper(
    chair_id: int,
    body: ArxivIngestRequest,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> ChairDocumentOut:
    """Fetch a paper from ArXiv by ID, embed its abstract, and attach it to the chair."""
    return await chair_service.ingest_arxiv_paper(chair_id, body)


@router.delete("/{chair_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chair_document(
    chair_id: int,
    doc_id: int,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> None:
    await chair_service.delete_document(chair_id, doc_id)
