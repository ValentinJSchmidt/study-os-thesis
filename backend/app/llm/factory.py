"""Factory functions for building LLMPort instances from application settings.

Two independent clients are constructed:
- Chat client   — used by ChatService and StudentService for text generation.
- Embed client  — used everywhere embeddings are needed (chairs, theses, students).

The split allows mixing providers, e.g. DeepSeek for chat and Ollama for
embeddings (DeepSeek does not currently offer a public embeddings endpoint).

Provider selection is controlled by ``LLM_CHAT_PROVIDER`` and
``LLM_EMBED_PROVIDER`` environment variables (both default to ``"ollama"``).

Supported providers
-------------------
chat  : ollama | azure | deepseek
embed : ollama | azure
"""

import logging

from app.config import Settings
from app.llm.ollama_client import OllamaClient
from app.llm.port import LLMPort

_logger = logging.getLogger(__name__)


def build_chat_client(settings: Settings) -> LLMPort:
    """Return an LLMPort configured for *chat* based on ``LLM_CHAT_PROVIDER``."""
    provider = settings.llm_chat_provider.strip().lower()
    _logger.info("Building chat client for provider=%r", provider)

    match provider:
        case "azure":
            from app.llm.litellm_adapter import LiteLLMAdapter  # lazy — avoids loading litellm at startup
            _require_setting(settings.azure_openai_endpoint, "AZURE_OPENAI_ENDPOINT")
            _require_setting(settings.azure_openai_api_key, "AZURE_OPENAI_API_KEY")
            _require_setting(settings.azure_chat_deployment, "AZURE_CHAT_DEPLOYMENT")
            return LiteLLMAdapter(
                chat_model=f"azure/{settings.azure_chat_deployment}",
                # embed is never called on the chat client, but the field is
                # required by the protocol; we set a sensible placeholder.
                embed_model=f"azure/{settings.azure_embed_deployment or settings.azure_chat_deployment}",
                chat_kwargs={
                    "api_base": settings.azure_openai_endpoint,
                    "api_key": settings.azure_openai_api_key,
                    "api_version": settings.azure_openai_api_version,
                },
            )

        case "deepseek":
            from app.llm.litellm_adapter import LiteLLMAdapter  # lazy — avoids loading litellm at startup
            _require_setting(settings.deepseek_api_key, "DEEPSEEK_API_KEY")
            return LiteLLMAdapter(
                chat_model=f"deepseek/{settings.deepseek_chat_model}",
                # DeepSeek has no public embeddings endpoint; embed calls on
                # this client will raise an error at runtime (by design — use
                # a separate embed provider via LLM_EMBED_PROVIDER).
                embed_model=f"deepseek/{settings.deepseek_chat_model}",
                chat_kwargs={
                    "api_key": settings.deepseek_api_key,
                    "api_base": settings.deepseek_base_url,
                },
            )

        case "ollama" | _:
            if provider not in ("ollama",):
                _logger.warning(
                    "Unknown LLM_CHAT_PROVIDER=%r, falling back to 'ollama'", provider
                )
            return OllamaClient(host=settings.ollama_host)


def build_embed_client(settings: Settings) -> LLMPort:
    """Return an LLMPort configured for *embeddings* based on ``LLM_EMBED_PROVIDER``."""
    provider = settings.llm_embed_provider.strip().lower()
    _logger.info("Building embed client for provider=%r", provider)

    match provider:
        case "azure":
            from app.llm.litellm_adapter import LiteLLMAdapter  # lazy — avoids loading litellm at startup
            _require_setting(settings.azure_openai_endpoint, "AZURE_OPENAI_ENDPOINT")
            _require_setting(settings.azure_openai_api_key, "AZURE_OPENAI_API_KEY")
            _require_setting(settings.azure_embed_deployment, "AZURE_EMBED_DEPLOYMENT")
            return LiteLLMAdapter(
                # chat is never called on the embed client; placeholder.
                chat_model=f"azure/{settings.azure_chat_deployment or settings.azure_embed_deployment}",
                embed_model=f"azure/{settings.azure_embed_deployment}",
                embed_kwargs={
                    "api_base": settings.azure_openai_endpoint,
                    "api_key": settings.azure_openai_api_key,
                    "api_version": settings.azure_openai_api_version,
                },
            )

        case "ollama" | _:
            if provider not in ("ollama",):
                _logger.warning(
                    "Unknown LLM_EMBED_PROVIDER=%r, falling back to 'ollama'", provider
                )
            return OllamaClient(host=settings.ollama_host)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_setting(value: str, env_var: str) -> None:
    """Raise RuntimeError if *value* is empty (misconfigured env var)."""
    if not value.strip():
        raise RuntimeError(
            f"LLM provider configuration error: {env_var} is required but not set. "
            f"Add it to your .env file."
        )
