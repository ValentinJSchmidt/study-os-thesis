import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.admin import controller as admin_router
from app.auth import controller as auth_router
from app.chairs import controller as chairs_router
from app.chat import controller as chat_router
from app.jobs import controller as jobs_router
from app.proposals import controller as proposals_router
from app.ws import controller as ws_router
from app.students import controller as students_router
from app.theses import controller as theses_router
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
from app.llm.factory import build_chat_client, build_embed_client
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
        raise RuntimeError('JWT_SECRET is set to an insecure default. Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"')


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
        _logger.warning("Ollama is offline — embedding dimension not verified. Embed and chat endpoints will fail until Ollama is running.")
    except httpx.TimeoutException:
        _logger.warning("Ollama did not respond within the timeout — embedding dimension not verified.")
    except OllamaError as exc:
        _logger.warning(
            "Ollama embed probe failed — embedding dimension not verified. Embed and chat endpoints will fail until the model is available. (%s)",
            exc,
        )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    import asyncio

    from app.db import engine
    from app.ws.listener import redis_listener
    from app.ws.manager import ConnectionManager

    _validate_settings()
    settings = get_settings()

    # Build and store provider-specific clients for the app lifetime.
    chat_client = build_chat_client(settings)
    embed_client = build_embed_client(settings)
    app.state.llm_chat_client = chat_client
    app.state.llm_embed_client = embed_client

    # WebSocket connection manager + Redis Pub/Sub listener
    app.state.ws_manager = ConnectionManager()
    listener_task = asyncio.create_task(redis_listener(app.state.ws_manager, settings.redis_url))

    # Keep a reference to the embed client as OllamaClient for the dim check
    # (only applicable when the embed provider is Ollama).
    if isinstance(embed_client, OllamaClient):
        await _check_embed_dim(embed_client, settings)

    yield

    # Graceful shutdown
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass

    if hasattr(chat_client, "aclose"):
        await chat_client.aclose()
    if embed_client is not chat_client and hasattr(embed_client, "aclose"):
        await embed_client.aclose()
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
    app.include_router(jobs_router.router)
    app.include_router(ws_router.router)

    @app.get("/api/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
