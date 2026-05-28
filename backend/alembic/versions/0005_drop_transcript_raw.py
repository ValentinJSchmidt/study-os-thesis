"""Drop students.transcript_raw column

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("students", "transcript_raw")


def downgrade() -> None:
    op.add_column(
        "students",
        sa.Column("transcript_raw", sa.Text, nullable=True),
    )
