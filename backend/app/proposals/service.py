from app.models import Thesis
from app.theses.repository import ThesisRepository


class ProposalService:
    """Business logic for student thesis proposals."""

    def __init__(self, thesis_repo: ThesisRepository) -> None:
        self._thesis_repo = thesis_repo

    async def list_my_proposals(self, user_id: int) -> list[Thesis]:
        """Return all AI-generated proposals for a student."""
        return await self._thesis_repo.list_for_user(user_id)
