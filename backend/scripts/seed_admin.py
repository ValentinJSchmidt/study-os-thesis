"""Create the first admin user.

Usage:
    uv run python scripts/seed_admin.py admin@example.com 'a-strong-password'
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.auth.security import hash_password  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import User, UserRole  # noqa: E402


async def main(email: str, password: str) -> None:
    async with SessionLocal() as session:
        existing = await session.scalar(select(User).where(User.email == email))
        if existing:
            existing.password_hash = hash_password(password)
            existing.role = UserRole.admin
            await session.commit()
            print(f"Updated existing user {email} to admin.")
            return
        admin = User(email=email, password_hash=hash_password(password), role=UserRole.admin)
        session.add(admin)
        await session.commit()
        print(f"Created admin {email}.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: seed_admin.py <email> <password>", file=sys.stderr)
        sys.exit(2)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
