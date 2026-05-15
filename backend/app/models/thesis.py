import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

EMBEDDING_DIM = 768  # nomic-embed-text


class ThesisSource(str, enum.Enum):
    professor = "professor"
    student = "student"
    openalex = "openalex"


class Thesis(Base):
    __tablename__ = "theses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    submitter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[ThesisSource] = mapped_column(
        Enum(ThesisSource, name="thesis_source"), nullable=False
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
