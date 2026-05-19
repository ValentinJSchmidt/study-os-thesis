from fastapi import APIRouter

from app.dependencies import CurrentUserDep, ThesisRepoDep
from app.models import Thesis
from app.schemas.thesis import ThesisOut

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


@router.get("/mine", response_model=list[ThesisOut])
async def list_my_proposals(
    current_user: CurrentUserDep,
    thesis_repo: ThesisRepoDep,
) -> list[Thesis]:
    """Return all AI-generated proposals for the currently logged-in student."""
    return await thesis_repo.list_for_user(current_user.id)
