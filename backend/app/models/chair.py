import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.thesis import EMBEDDING_DIM


class ChairDocumentKind(str, enum.Enum):
    description = "description"
    paper = "paper"


class Chair(Base):
    """A university research chair / group."""

    __tablename__ = "chairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    professor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Optional link to a registered professor account.
    professor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    documents: Mapped[list["ChairDocument"]] = relationship("ChairDocument", back_populates="chair", cascade="all, delete-orphan")


class ChairDocument(Base):
    """One embeddable document associated with a chair.

    Each row holds either the chair's short description or a paper abstract,
    along with its vector embedding for ANN search.
    """

    __tablename__ = "chair_documents"
    __table_args__ = (
        # Prevent the same ArXiv paper from being added twice to the same chair.
        UniqueConstraint("chair_id", "arxiv_id", name="uq_chair_documents_chair_arxiv"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chair_id: Mapped[int] = mapped_column(ForeignKey("chairs.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[ChairDocumentKind] = mapped_column(Enum(ChairDocumentKind, name="chair_document_kind"), nullable=False)
    # Paper title (null for description documents).
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # The text that was embedded.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # ArXiv identifier (e.g. "2301.07041"), null for description documents.
    arxiv_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    published_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chair: Mapped["Chair"] = relationship("Chair", back_populates="documents")
