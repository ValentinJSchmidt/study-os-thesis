from fastapi import APIRouter, Request, status

from app.dependencies import AuthServiceDep, CurrentUserDep
from app.limiter import limiter
from app.models import User
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, body: RegisterRequest, auth_service: AuthServiceDep) -> User:
    return await auth_service.register(body)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.login(body)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUserDep) -> User:
    return user
