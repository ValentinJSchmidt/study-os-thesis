from fastapi import APIRouter, Form, Query, UploadFile, status

from app.auth.deps import CurrentUserDep
from app.exceptions import BadRequestException, ForbiddenException
from app.models import UserRole
from app.students.deps import StudentServiceDep
from app.students.schemas import StudentOut

router = APIRouter(prefix="/api/students", tags=["students"])

_MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/me", response_model=StudentOut)
async def get_my_profile(
    current_user: CurrentUserDep,
    student_service: StudentServiceDep,
) -> StudentOut:
    if current_user.role != UserRole.student:
        raise ForbiddenException("Only students have an academic profile.")
    return await student_service.get_profile(current_user.id)


@router.post("/me/transcript", response_model=StudentOut, status_code=status.HTTP_200_OK)
async def upload_transcript(
    current_user: CurrentUserDep,
    student_service: StudentServiceDep,
    file: UploadFile,
    program: str | None = Form(default=None, max_length=255),
    semester: int | None = Form(default=None, ge=1, le=30),
) -> StudentOut:
    """Upload a PDF transcript of records.

    The file is parsed with pdfplumber and the text is sent to the LLM for
    structured extraction (courses, grades, ECTS credits). The student's
    profile and course list are then upserted in the DB.
    """
    if current_user.role != UserRole.student:
        raise ForbiddenException("Only students can upload a transcript.")

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise BadRequestException("Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_PDF_SIZE:
        raise BadRequestException("PDF exceeds the 10 MB size limit.")
    if not pdf_bytes:
        raise BadRequestException("Uploaded file is empty.")

    return await student_service.upload_transcript(
        user_id=current_user.id,
        pdf_bytes=pdf_bytes,
        program=program,
        semester=semester,
    )
