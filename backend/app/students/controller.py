from fastapi import APIRouter, Form, UploadFile, status

from app.auth.deps import CurrentUserDep
from app.exceptions import BadRequestException
from app.jobs.deps import JobServiceDep
from app.models.job import JobType
from app.students.deps import StudentServiceDep
from app.students.schemas import StudentOut

router = APIRouter(prefix="/api/students", tags=["students"])

_MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/me", response_model=StudentOut)
async def get_my_profile(
    current_user: CurrentUserDep,
    student_service: StudentServiceDep,
) -> object:
    return await student_service.get_profile(current_user.id)


@router.post("/me/transcript", status_code=status.HTTP_202_ACCEPTED)
async def upload_transcript(
    current_user: CurrentUserDep,
    job_service: JobServiceDep,
    file: UploadFile,
    program: str | None = Form(default=None, max_length=255),
    semester: int | None = Form(default=None, ge=1, le=30),
) -> dict:
    """Upload a PDF transcript. Processing is dispatched to a background worker."""
    from app.config import get_settings
    from app.students.pdf_store import store_pdf
    from app.students.tasks import parse_transcript

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise BadRequestException("Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_PDF_SIZE:
        raise BadRequestException("PDF exceeds the 10 MB size limit.")
    if not pdf_bytes:
        raise BadRequestException("Uploaded file is empty.")

    # Create the job first, stash the PDF bytes under its id, then dispatch.
    job = await job_service.create_job(
        type=JobType.parse_transcript,
        user_id=current_user.id,
        input_data={"program": program, "semester": semester},
    )
    await store_pdf(get_settings().redis_url, str(job.id), pdf_bytes)

    task_result = parse_transcript.delay(
        user_id=current_user.id,
        job_id=str(job.id),
        program=program,
        semester=semester,
    )
    await job_service.set_celery_task_id(job.id, task_result.id)

    return {"job_id": str(job.id)}
