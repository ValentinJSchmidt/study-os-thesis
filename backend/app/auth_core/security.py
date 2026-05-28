import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from app.config import get_settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password_sync(plain: str) -> str:
    return _pwd.hash(plain)


def _verify_password_sync(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


async def hash_password(plain: str) -> str:
    """Hash a password in a thread executor to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _hash_password_sync, plain)


async def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password in a thread executor to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_verify_password_sync, plain, hashed))


def create_access_token(sub: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError:
        return None
