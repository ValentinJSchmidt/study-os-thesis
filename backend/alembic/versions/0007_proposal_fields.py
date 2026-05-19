"""Add difficulty, skills_required, generated_for_user_id, chat_session_id to theses

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE thesis_difficulty AS ENUM ('bachelor', 'master', 'phd')"
    )
    op.add_column(
        "theses",
        sa.Column(
            "difficulty",
            sa.Enum("bachelor", "master", "phd", name="thesis_difficulty"),
            nullable=True,
        ),
    )
    op.add_column(
        "theses",
        sa.Column("skills_required", JSONB, nullable=True),
    )
    op.add_column(
        "theses",
        sa.Column(
            "generated_for_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_theses_generated_for_user_id",
        "theses",
        ["generated_for_user_id"],
    )
    op.add_column(
        "theses",
        sa.Column(
            "chat_session_id",
            sa.Integer,
            sa.ForeignKey("chat_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("theses", "chat_session_id")
    op.drop_index("ix_theses_generated_for_user_id", table_name="theses")
    op.drop_column("theses", "generated_for_user_id")
    op.drop_column("theses", "skills_required")
    op.drop_column("theses", "difficulty")
    op.execute("DROP TYPE IF EXISTS thesis_difficulty")
