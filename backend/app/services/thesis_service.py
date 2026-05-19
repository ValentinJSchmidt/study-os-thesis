from app.exceptions import BadRequestException, NotFoundException
from app.llm.ollama_client import OllamaClient
from app.config import Settings
from app.models import Thesis, ThesisSource, User, UserRole
from app.repositories.thesis_repository import ThesisRepository
from app.repositories.user_repository import UserRepository
from app.schemas.thesis import ThesisCreate


class ThesisService:
    """Business logic for thesis management."""

    def __init__(
        self,
        thesis_repo: ThesisRepository,
        user_repo: UserRepository,
        ollama_client: OllamaClient,
        settings: Settings,
    ) -> None:
        self._thesis_repo = thesis_repo
        self._user_repo = user_repo
        self._ollama = ollama_client
        self._settings = settings

    async def create_thesis(self, data: ThesisCreate, user: User) -> Thesis:
        if data.supervisor_id is not None:
            supervisor = await self._user_repo.get_by_id(data.supervisor_id)
            if not supervisor or supervisor.role != UserRole.professor:
                raise BadRequestException("supervisor_id must reference a professor")

        source = ThesisSource.professor if user.role == UserRole.professor else ThesisSource.student

        embedding = await self._ollama.embed(
            self._settings.ollama_embed_model,
            f"{data.title}\n\n{data.abstract}",
        )

        thesis = await self._thesis_repo.create(
            title=data.title,
            abstract=data.abstract,
            submitter_id=user.id,
            source=source,
            supervisor_id=data.supervisor_id,
            chair_id=data.chair_id,
            embedding=embedding,
        )
        await self._thesis_repo.commit()
        return thesis

    async def list_theses(self, limit: int = 20, offset: int = 0) -> list[Thesis]:
        return await self._thesis_repo.list(limit=limit, offset=offset)

    async def get_thesis(self, thesis_id: int) -> Thesis:
        thesis = await self._thesis_repo.get_by_id(thesis_id)
        if not thesis:
            raise NotFoundException("Thesis", thesis_id)
        return thesis
