from typing import Annotated

from fastapi import Depends

from app.auth.deps import LLMEmbedClientDep, SessionDep, SettingsDep, UserRepoDep
from app.theses.repository import ThesisRepository
from app.theses.service import ThesisService


def get_thesis_repository(session: SessionDep) -> ThesisRepository:
    return ThesisRepository(session)


ThesisRepoDep = Annotated[ThesisRepository, Depends(get_thesis_repository)]


def get_thesis_service(
    thesis_repo: ThesisRepoDep,
    user_repo: UserRepoDep,
    embed_client: LLMEmbedClientDep,
    settings: SettingsDep,
) -> ThesisService:
    return ThesisService(thesis_repo, user_repo, embed_client, settings)


ThesisServiceDep = Annotated[ThesisService, Depends(get_thesis_service)]
