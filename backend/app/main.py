import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admin as admin_router
from app.api import auth as auth_router
from app.api import chairs as chairs_router
from app.api import chat as chat_router
from app.api import proposals as proposals_router
from app.api import students as students_router
from app.api import theses as theses_router
from app.config import Settings, get_settings
from app.exceptions import (
    AlreadyExistsException,
    AppException,
    BadRequestException,
    ForbiddenException,
    InvalidCredentialsException,
    NotFoundException,
    UnauthorizedException,
)
from app.limiter import limiter
from app.llm.ollama_client import OllamaClient, OllamaError

_logger = logging.getLogger(__name__)


def _status_code_for(exc: AppException) -> int:
    """Map domain exception types to HTTP status codes."""
    mapping: dict[type, int] = {
        NotFoundException: 404,
        AlreadyExistsException: 409,
        InvalidCredentialsException: 401,
        UnauthorizedException: 401,
        ForbiddenException: 403,
        BadRequestException: 400,
    }
    return mapping.get(type(exc), 500)


def _validate_settings() -> None:
    """Fail fast on known-dangerous default values."""
    settings = get_settings()
    if settings.jwt_secret in ("change-me-to-a-random-string", "", "secret"):
        raise RuntimeError(
            "JWT_SECRET is set to an insecure default. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )


async def _check_embed_dim(ollama_client: OllamaClient, settings: Settings) -> None:
    """Probe Ollama to verify the embedding dimension matches OLLAMA_EMBED_DIM.

    - If Ollama is reachable and the dimension is wrong  → hard RuntimeError.
    - If Ollama is unreachable (offline / not yet started) → log a warning and
      continue; embed/chat endpoints will fail at request time, which is the
      expected behaviour when Ollama is down.
    """
    try:
        probe = await ollama_client.embed(settings.ollama_embed_model, "dim check")
        actual = len(probe)
        if actual != settings.ollama_embed_dim:
            raise RuntimeError(
                f"OLLAMA_EMBED_MODEL '{settings.ollama_embed_model}' produces "
                f"{actual}-dimensional vectors but OLLAMA_EMBED_DIM={settings.ollama_embed_dim}. "
                f"Update OLLAMA_EMBED_DIM in your .env to {actual}."
            )
        _logger.info(
            "Ollama embed dim check passed: model=%s dim=%d",
            settings.ollama_embed_model,
            actual,
        )
    except httpx.ConnectError:
        _logger.warning(
            "Ollama is offline — embedding dimension not verified. "
            "Embed and chat endpoints will fail until Ollama is running."
        )
    except httpx.TimeoutException:
        _logger.warning(
            "Ollama did not respond within the timeout — embedding dimension not verified."
        )
    except OllamaError as exc:
        _logger.warning(
            "Ollama embed probe failed — embedding dimension not verified. "
            "Embed and chat endpoints will fail until the model is available. (%s)",
            exc,
        )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    from app.db import engine

    _validate_settings()
    settings = get_settings()

    # Create and store a single shared Ollama client for the app lifetime.
    ollama_client = OllamaClient()
    app.state.ollama_client = ollama_client

    # Verify embedding dimension — soft warn if Ollama is offline.
    await _check_embed_dim(ollama_client, settings)

    yield

    # Graceful shutdown: close HTTP connection pool and DB engine.
    await ollama_client.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="study-os-thesis API", lifespan=_lifespan)

    # ---- Rate limiting ----
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Global exception handler for domain exceptions ----
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=_status_code_for(exc),
            content={"detail": exc.detail},
        )

    # ---- Catch-all: log every unhandled exception before returning 500 ----
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        _logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ---- Routers ----
    app.include_router(auth_router.router)
    app.include_router(theses_router.router)
    app.include_router(chat_router.router)
    app.include_router(admin_router.router)
    app.include_router(students_router.router)
    app.include_router(chairs_router.router)
    app.include_router(proposals_router.router)

    @app.get("/api/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
