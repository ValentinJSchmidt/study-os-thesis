from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.deps import CurrentUserDep, require_role
from app.chairs.deps import ChairServiceDep
from app.chairs.schemas import ArxivIngestRequest, ChairCreate, ChairOut, ChairPatch
from app.jobs.deps import JobServiceDep
from app.models import User, UserRole
from app.models.job import JobType

router = APIRouter(prefix="/api/chairs", tags=["chairs"])

AdminDep = Annotated[User, Depends(require_role(UserRole.admin))]


@router.get("", response_model=list[ChairOut])
async def list_chairs(
    _user: CurrentUserDep,
    chair_service: ChairServiceDep,
) -> list:
    return await chair_service.list_chairs()


@router.get("/{chair_id}", response_model=ChairOut)
async def get_chair(
    chair_id: int,
    _user: CurrentUserDep,
    chair_service: ChairServiceDep,
) -> object:
    return await chair_service.get_chair(chair_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_chair(
    body: ChairCreate,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
    job_service: JobServiceDep,
) -> dict:
    """Create a chair and dispatch description embedding to a background worker."""
    from app.chairs.tasks import embed_chair_description

    # Persist the chair immediately; the worker embeds its description.
    chair = await chair_service.create_chair(body, embed=False)

    job = await job_service.create_job(
        type=JobType.embed_chair,
        user_id=_admin.id,
        input_data={"chair_id": chair.id},
    )
    task_result = embed_chair_description.delay(chair.id, _admin.id, str(job.id))
    await job_service.set_celery_task_id(job.id, task_result.id)

    out = ChairOut.model_validate(chair)
    return {**out.model_dump(mode="json"), "job_id": str(job.id)}


@router.patch("/{chair_id}", response_model=ChairOut)
async def update_chair(
    chair_id: int,
    body: ChairPatch,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> object:
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
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_arxiv_paper(
    chair_id: int,
    body: ArxivIngestRequest,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
    job_service: JobServiceDep,
) -> dict:
    """Dispatch ArXiv paper ingestion to a background worker."""
    from app.chairs.tasks import ingest_arxiv_paper as ingest_task

    # Validate chair exists before dispatching
    await chair_service.get_chair(chair_id)

    job = await job_service.create_job(
        type=JobType.ingest_arxiv,
        user_id=_admin.id,
        input_data={"chair_id": chair_id, "arxiv_id": body.arxiv_id},
    )
    task_result = ingest_task.delay(chair_id, body.arxiv_id, _admin.id, str(job.id))
    await job_service.set_celery_task_id(job.id, task_result.id)

    return {"job_id": str(job.id), "chair_id": chair_id, "arxiv_id": body.arxiv_id}


@router.delete("/{chair_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chair_document(
    chair_id: int,
    doc_id: int,
    _admin: AdminDep,
    chair_service: ChairServiceDep,
) -> None:
    await chair_service.delete_document(chair_id, doc_id)
