"""Drop professor from user_role enum

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-28
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Re-assign any existing professor users to student before dropping the value
    op.execute("UPDATE users SET role = 'student' WHERE role = 'professor'")

    # PostgreSQL does not support DROP VALUE from an enum directly.
    # The safest approach is to recreate the column with the new enum type.
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('student', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")


def downgrade() -> None:
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('student', 'professor', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")
