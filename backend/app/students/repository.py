from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student, StudentCourse
from app.students.schemas import StudentCourseItem


class StudentRepository:
    """Data-access layer for the `students` and `student_courses` tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> Student | None:
        result = await self._session.scalar(
            select(Student)
            .where(Student.user_id == user_id)
            .options(selectinload(Student.courses))
        )
        return result

    async def upsert(
        self,
        user_id: int,
        *,
        gpa: float | None,
        program: str | None,
        semester: int | None,
        profile_embedding: list[float] | None,
        courses: list[StudentCourseItem],
    ) -> Student:
        student = await self._session.get(Student, user_id)
        if student is None:
            student = Student(user_id=user_id)
            self._session.add(student)

        student.gpa = gpa
        student.program = program
        student.semester = semester
        student.profile_embedding = profile_embedding
        student.updated_at = datetime.now(timezone.utc)

        # Replace all existing courses atomically.
        await self._session.execute(
            delete(StudentCourse).where(StudentCourse.student_id == user_id)
        )
        for item in courses:
            self._session.add(
                StudentCourse(
                    student_id=user_id,
                    course_name=item.course_name,
                    credits=item.credits,
                    grade=item.grade,
                    semester_taken=item.semester_taken,
                )
            )

        await self._session.flush()
        await self._session.refresh(student)
        return student

    async def commit(self) -> None:
        await self._session.commit()
