from app.config import get_settings
from app.llm.ollama_client import OllamaClient


async def embed_text(text: str) -> list[float]:
    """Embed a single string with the configured embedding model."""
    settings = get_settings()
    client = OllamaClient()
    return await client.embed(settings.ollama_embed_model, text)
