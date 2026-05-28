from typing import Annotated

from fastapi import Depends

from app.auth.deps import LLMChatClientDep, LLMEmbedClientDep, SessionDep, SettingsDep
from app.students.repository import StudentRepository
from app.students.service import StudentService


def get_student_repository(session: SessionDep) -> StudentRepository:
    return StudentRepository(session)


StudentRepoDep = Annotated[StudentRepository, Depends(get_student_repository)]


def get_student_service(
    student_repo: StudentRepoDep,
    chat_client: LLMChatClientDep,
    embed_client: LLMEmbedClientDep,
    settings: SettingsDep,
) -> StudentService:
    return StudentService(student_repo, chat_client, embed_client, settings)


StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]
