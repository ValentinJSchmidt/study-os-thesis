"""Add chairs, chair_documents, students, student_courses; add chair_id to theses

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    # ------------------------------------------------------------------
    # chairs
    # ------------------------------------------------------------------
    op.create_table(
        "chairs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_description", sa.Text, nullable=False),
        sa.Column("professor_name", sa.String(255), nullable=False),
        sa.Column(
            "professor_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # chair_documents
    # ------------------------------------------------------------------
    op.create_table(
        "chair_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "chair_id",
            sa.Integer,
            sa.ForeignKey("chairs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "kind",
            sa.Enum("description", "paper", name="chair_document_kind"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("arxiv_id", sa.String(50), nullable=True),
        sa.Column("published_year", sa.SmallInteger, nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("chair_id", "arxiv_id", name="uq_chair_documents_chair_arxiv"),
    )

    # HNSW index for fast ANN search on chair document embeddings.
    op.execute(
        """
        CREATE INDEX ix_chair_documents_embedding_hnsw
        ON chair_documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # ------------------------------------------------------------------
    # students
    # ------------------------------------------------------------------
    op.create_table(
        "students",
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("program", sa.String(255), nullable=True),
        sa.Column("semester", sa.SmallInteger, nullable=True),
        sa.Column("gpa", sa.Numeric(3, 2), nullable=True),
        sa.Column("transcript_raw", sa.Text, nullable=True),
        sa.Column("profile_embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # student_courses
    # ------------------------------------------------------------------
    op.create_table(
        "student_courses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer,
            sa.ForeignKey("students.user_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("course_name", sa.String(255), nullable=False),
        sa.Column("credits", sa.Numeric(4, 1), nullable=True),
        sa.Column("grade", sa.String(20), nullable=True),
        sa.Column("semester_taken", sa.String(50), nullable=True),
    )

    # ------------------------------------------------------------------
    # theses: add chair_id FK
    # ------------------------------------------------------------------
    op.add_column(
        "theses",
        sa.Column(
            "chair_id",
            sa.Integer,
            sa.ForeignKey("chairs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_theses_chair_id", "theses", ["chair_id"])


def downgrade() -> None:
    op.drop_index("ix_theses_chair_id", table_name="theses")
    op.drop_column("theses", "chair_id")

    op.drop_table("student_courses")
    op.drop_table("students")

    op.execute("DROP INDEX IF EXISTS ix_chair_documents_embedding_hnsw")
    op.drop_table("chair_documents")
    op.execute("DROP TYPE IF EXISTS chair_document_kind")

    op.drop_table("chairs")
