from fastapi import APIRouter, status

from app.auth.deps import CurrentUserDep
from app.chat.deps import ChatServiceDep
from app.chat.schemas import MessageIn, MessageOut, SendMessageResponse, SessionOut
from app.jobs.deps import JobServiceDep
from app.models import ChatMessage, ChatSession
from app.models.job import JobType

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> ChatSession:
    return await chat_service.create_session(user.id)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> list[ChatSession]:
    return await chat_service.list_sessions(user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: int,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> list[ChatMessage]:
    return await chat_service.get_messages(session_id, user.id)


@router.post(
    "/sessions/{session_id}/messages",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_message(
    session_id: int,
    body: MessageIn,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
    job_service: JobServiceDep,
) -> dict:
    """Accept a user message and dispatch the agent loop to a background worker."""
    from app.chat.tasks import process_chat_turn

    # Validate session ownership and persist user message eagerly
    # (The service will validate ownership)
    chat = await chat_service._chat_repo.get_session(session_id)
    if not chat or chat.user_id != user.id:
        from app.exceptions import NotFoundException
        raise NotFoundException("Session", session_id)

    job = await job_service.create_job(
        type=JobType.chat_turn,
        user_id=user.id,
        input_data={"session_id": session_id, "content": body.content[:200]},
    )
    task_result = process_chat_turn.delay(
        session_id=session_id,
        user_id=user.id,
        content=body.content,
        job_id=str(job.id),
    )
    await job_service.set_celery_task_id(job.id, task_result.id)

    return {"job_id": str(job.id), "session_id": session_id}
