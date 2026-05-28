from typing import Annotated

from fastapi import Depends

from app.auth.deps import LLMChatClientDep, LLMEmbedClientDep, SessionDep, SettingsDep
from app.chairs.deps import ChairRepoDep
from app.chat.repository import ChatRepository
from app.chat.service import ChatService
from app.students.deps import StudentRepoDep
from app.theses.deps import ThesisRepoDep


def get_chat_repository(session: SessionDep) -> ChatRepository:
    return ChatRepository(session)


ChatRepoDep = Annotated[ChatRepository, Depends(get_chat_repository)]


def get_chat_service(
    chat_repo: ChatRepoDep,
    chat_client: LLMChatClientDep,
    embed_client: LLMEmbedClientDep,
    settings: SettingsDep,
    student_repo: StudentRepoDep,
    chair_repo: ChairRepoDep,
    thesis_repo: ThesisRepoDep,
) -> ChatService:
    return ChatService(
        chat_repo, chat_client, embed_client, settings,
        student_repo=student_repo,
        chair_repo=chair_repo,
        thesis_repo=thesis_repo,
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
