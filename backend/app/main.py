from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin as admin_router
from app.api import auth as auth_router
from app.api import chat as chat_router
from app.api import theses as theses_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="study-os-thesis API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router.router)
    app.include_router(theses_router.router)
    app.include_router(chat_router.router)
    app.include_router(admin_router.router)

    @app.get("/api/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
