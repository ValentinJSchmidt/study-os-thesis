from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth.deps import CurrentUserDep, require_role
from app.jobs.deps import JobServiceDep
from app.models import User, UserRole
from app.models.job import JobType
from app.theses.deps import ThesisServiceDep
from app.theses.schemas import ThesisCreate, ThesisOut

router = APIRouter(prefix="/api/theses", tags=["theses"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thesis(
    body: ThesisCreate,
    user: Annotated[User, Depends(require_role(UserRole.admin))],
    thesis_service: ThesisServiceDep,
    job_service: JobServiceDep,
) -> dict:
    """Create a thesis and dispatch embedding to a background worker."""
    from app.theses.tasks import embed_thesis

    # Persist thesis immediately; the worker generates the embedding.
    thesis = await thesis_service.create_thesis(body, user, embed=False)

    # Create the job first so the worker receives the real job id.
    job = await job_service.create_job(
        type=JobType.embed_thesis,
        user_id=user.id,
        input_data={"thesis_id": thesis.id},
    )
    task_result = embed_thesis.delay(thesis.id, user.id, str(job.id))
    await job_service.set_celery_task_id(job.id, task_result.id)

    out = ThesisOut.model_validate(thesis)
    return {**out.model_dump(mode="json"), "job_id": str(job.id)}


@router.get("", response_model=list[ThesisOut])
async def list_theses(
    _user: CurrentUserDep,
    thesis_service: ThesisServiceDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list:
    return await thesis_service.list_theses(limit=limit, offset=offset)


@router.get("/{thesis_id}", response_model=ThesisOut)
async def get_thesis(
    thesis_id: int,
    _user: CurrentUserDep,
    thesis_service: ThesisServiceDep,
) -> object:
    return await thesis_service.get_thesis(thesis_id)
