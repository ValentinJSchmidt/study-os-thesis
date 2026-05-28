from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")

    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expires_minutes: int = Field(60, alias="JWT_EXPIRES_MINUTES")

    # ---------------------------------------------------------------------------
    # Provider selection
    # ---------------------------------------------------------------------------
    # Supported chat providers  : ollama | azure | deepseek
    # Supported embed providers : ollama | azure
    # The two can be mixed independently, e.g. deepseek for chat + ollama for embed.
    llm_chat_provider: str = Field("ollama", alias="LLM_CHAT_PROVIDER")
    llm_embed_provider: str = Field("ollama", alias="LLM_EMBED_PROVIDER")

    # ---------------------------------------------------------------------------
    # Ollama (default provider)
    # ---------------------------------------------------------------------------
    ollama_host: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_chat_model: str = Field("gemma4:26b", alias="OLLAMA_CHAT_MODEL")
    # Model used for transcript extraction. Defaults to OLLAMA_CHAT_MODEL if not set.
    ollama_extract_model: str = Field("", alias="OLLAMA_EXTRACT_MODEL")
    ollama_embed_model: str = Field("qwen3-embedding:4b", alias="OLLAMA_EMBED_MODEL")
    # Must match the output dimension of OLLAMA_EMBED_MODEL.
    # Common values: qwen3-embedding:4b=2560, nomic-embed-text=768, mxbai-embed-large=1024
    ollama_embed_dim: int = Field(2560, alias="OLLAMA_EMBED_DIM")

    @property
    def effective_extract_model(self) -> str:
        """Returns OLLAMA_EXTRACT_MODEL if set, otherwise falls back to OLLAMA_CHAT_MODEL."""
        return self.ollama_extract_model.strip() or self.ollama_chat_model

    # ---------------------------------------------------------------------------
    # Azure OpenAI  (LLM_CHAT_PROVIDER=azure or LLM_EMBED_PROVIDER=azure)
    # ---------------------------------------------------------------------------
    azure_openai_endpoint: str = Field("", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field("", alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field("2024-02-01", alias="AZURE_OPENAI_API_VERSION")
    # Deployment name for chat/completion calls (e.g. "gpt-4o")
    azure_chat_deployment: str = Field("", alias="AZURE_CHAT_DEPLOYMENT")
    # Deployment name for embedding calls (e.g. "text-embedding-3-small")
    azure_embed_deployment: str = Field("", alias="AZURE_EMBED_DEPLOYMENT")

    # ---------------------------------------------------------------------------
    # DeepSeek  (LLM_CHAT_PROVIDER=deepseek — chat only, no embeddings)
    # ---------------------------------------------------------------------------
    deepseek_api_key: str = Field("", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_chat_model: str = Field("deepseek-chat", alias="DEEPSEEK_CHAT_MODEL")

    # ---------------------------------------------------------------------------
    # CORS
    # ---------------------------------------------------------------------------
    cors_origins: str = Field("http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
