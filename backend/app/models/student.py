from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.thesis import EMBEDDING_DIM


class Student(Base):
    """Academic profile for a user with role=student (1-to-1 with users)."""

    __tablename__ = "students"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    program: Mapped[str | None] = mapped_column(String(255), nullable=True)
    semester: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # Credit-weighted average of German grades (1.0 best, 5.0 fail).
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    # Pre-computed embedding of concatenated course names for chair search.
    profile_embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    courses: Mapped[list["StudentCourse"]] = relationship("StudentCourse", back_populates="student", cascade="all, delete-orphan")


class StudentCourse(Base):
    """One course row parsed from a student's transcript."""

    __tablename__ = "student_courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.user_id", ondelete="CASCADE"), nullable=False, index=True)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Credits as decimal (e.g. 7.5 ECTS).
    credits: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    # Raw grade string: "1,3", "2,0", "bestanden", "nicht bestanden", etc.
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # e.g. "WS 2023/24", "SS 2024"
    semester_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="courses")
