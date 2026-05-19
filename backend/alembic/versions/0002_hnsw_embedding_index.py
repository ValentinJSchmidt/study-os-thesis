"""Add HNSW index on theses.embedding for fast cosine similarity search

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # HNSW index for approximate nearest-neighbour cosine similarity search.
    # vector_cosine_ops matches the cosine_distance operator used in search_theses.py.
    # CREATE INDEX CONCURRENTLY is not supported inside a transaction block, so we
    # use op.execute with the non-concurrent form (safe during a migration).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_theses_embedding_hnsw
        ON theses
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_theses_embedding_hnsw")
