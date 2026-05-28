from typing import Annotated

from fastapi import Depends

from app.auth.deps import LLMEmbedClientDep, SessionDep, SettingsDep
from app.chairs.repository import ChairRepository
from app.chairs.service import ChairService


def get_chair_repository(session: SessionDep) -> ChairRepository:
    return ChairRepository(session)


ChairRepoDep = Annotated[ChairRepository, Depends(get_chair_repository)]


def get_chair_service(
    chair_repo: ChairRepoDep,
    embed_client: LLMEmbedClientDep,
    settings: SettingsDep,
) -> ChairService:
    return ChairService(chair_repo, embed_client, settings)


ChairServiceDep = Annotated[ChairService, Depends(get_chair_service)]
