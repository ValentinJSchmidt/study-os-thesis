from app.config import get_settings
from app.llm.factory import build_embed_client


async def embed_text(text: str) -> list[float]:
    """Embed a single string with the configured embedding model.

    Uses the embed client configured via LLM_EMBED_PROVIDER (default: ollama).
    A new client instance is created per call — this helper is intended for
    one-off embeddings outside of the request lifecycle (e.g. scripts/seeds).
    For request-scoped code prefer injecting LLMEmbedClientDep via FastAPI DI.
    """
    settings = get_settings()
    client = build_embed_client(settings)
    try:
        return await client.embed(settings.ollama_embed_model, text)
    finally:
        await client.aclose()
