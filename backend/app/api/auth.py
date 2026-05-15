from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.db import get_session
from app.models import User, UserRole
from app.schemas.user import RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if body.role == UserRole.admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Admin cannot self-register")
    existing = await session.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=body.email, password_hash=hash_password(body.password), role=body.role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    token = create_access_token(sub=str(user.id), extra={"role": user.role.value})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
