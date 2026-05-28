from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentCourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_name: str
    credits: float | None
    grade: str | None
    semester_taken: str | None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    program: str | None
    semester: int | None
    gpa: float | None
    updated_at: datetime
    courses: list[StudentCourseOut] = []


class StudentCourseItem(BaseModel):
    """One course row as extracted from the transcript by the LLM."""

    model_config = ConfigDict(extra="ignore")

    course_name: str = Field(min_length=1, max_length=255)
    credits: float | None = None
    grade: str | None = Field(default=None, max_length=50)
    semester_taken: str | None = Field(default=None, max_length=50)


class TranscriptParseResult(BaseModel):
    """Internal: validated LLM output for a transcript upload."""

    gpa: float | None = None
    courses: list[StudentCourseItem] = []
