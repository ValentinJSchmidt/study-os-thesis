"""Resize all vector columns from 768 to 2560 (qwen3-embedding:4b)

Existing embeddings are invalidated by the dimension change and must be
re-computed after this migration. All vector columns are dropped and
re-added as nullable so no data loss occurs for non-vector fields.

NOTE: pgvector HNSW indexes support a maximum of 2000 dimensions.
At 2560 dims we use exact cosine search (sequential scan with the <=>
operator). This is acceptable at research-project scale; for larger
datasets an IVFFlat index (max 2000 dims) or dimensionality reduction
would be needed.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_DIM = 768
NEW_DIM = 2560


def upgrade() -> None:
    # ── theses.embedding ─────────────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_theses_embedding_hnsw")
    op.drop_column("theses", "embedding")
    op.add_column("theses", sa.Column("embedding", Vector(NEW_DIM), nullable=True))
    # No ANN index: 2560 dims exceeds pgvector HNSW/IVFFlat limit of 2000.
    # Cosine search uses an exact sequential scan (<=> operator).

    # ── chair_documents.embedding ─────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_chair_documents_embedding_hnsw")
    op.drop_column("chair_documents", "embedding")
    op.add_column("chair_documents", sa.Column("embedding", Vector(NEW_DIM), nullable=True))

    # ── students.profile_embedding ────────────────────────────────────────────
    op.drop_column("students", "profile_embedding")
    op.add_column("students", sa.Column("profile_embedding", Vector(NEW_DIM), nullable=True))


def downgrade() -> None:
    # ── students.profile_embedding ────────────────────────────────────────────
    op.drop_column("students", "profile_embedding")
    op.add_column("students", sa.Column("profile_embedding", Vector(OLD_DIM), nullable=True))

    # ── chair_documents.embedding ─────────────────────────────────────────────
    op.drop_column("chair_documents", "embedding")
    op.add_column("chair_documents", sa.Column("embedding", Vector(OLD_DIM), nullable=True))
    op.execute(
        """
        CREATE INDEX ix_chair_documents_embedding_hnsw
        ON chair_documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # ── theses.embedding ─────────────────────────────────────────────────────
    op.drop_column("theses", "embedding")
    op.add_column("theses", sa.Column("embedding", Vector(OLD_DIM), nullable=True))
    op.execute(
        """
        CREATE INDEX ix_theses_embedding_hnsw
        ON theses
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
