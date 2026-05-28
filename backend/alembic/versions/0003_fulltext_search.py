"""Add full-text search: search_vec generated tsvector column + GIN index

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-19

The `search_vec` column is a STORED generated column — Postgres recomputes it
automatically on every INSERT/UPDATE, so no application code needs to maintain it.
It concatenates `title` and `abstract` and converts them to a tsvector using the
'english' dictionary (stemming, stop-word removal).

A GIN index is added to make full-text queries using `@@` fast.

Together with the HNSW index on `embedding` (migration 0002), this enables
hybrid search: vector similarity + BM25 keyword ranking fused via RRF.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Generated STORED column: recomputed by Postgres on every write.
    op.execute(
        """
        ALTER TABLE theses
          ADD COLUMN search_vec tsvector
            GENERATED ALWAYS AS (
              to_tsvector(
                'english',
                coalesce(title, '') || ' ' || coalesce(abstract, '')
              )
            ) STORED
        """
    )
    # GIN index for fast full-text `@@` queries.
    op.execute("CREATE INDEX ix_theses_search_vec_gin ON theses USING gin(search_vec)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_theses_search_vec_gin")
    op.execute("ALTER TABLE theses DROP COLUMN IF EXISTS search_vec")
