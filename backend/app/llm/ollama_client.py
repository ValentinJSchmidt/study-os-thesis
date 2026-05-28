from typing import Any

import httpx

from app.config import get_settings


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    """Async Ollama API client with a persistent connection pool.

    A single `httpx.AsyncClient` is reused across all requests so that TCP
    connections are pooled rather than created and torn down on every call.
    Call `aclose()` (or use as an async context manager) to release resources.
    """

    def __init__(self, host: str | None = None, timeout: float = 600.0):
        s = get_settings()
        self.host = (host or s.ollama_host).rstrip("/")
        self.timeout = timeout
        # Persistent client — reused for the lifetime of this instance.
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def embed(self, model: str, text: str) -> list[float]:
        """Return one embedding vector for `text` using Ollama's /api/embed."""
        try:
            r = await self._client.post(
                f"{self.host}/api/embed",
                json={"model": model, "input": text},
            )
        except httpx.ConnectError as exc:
            raise OllamaError(f"Ollama not reachable at {self.host}") from exc
        except httpx.TimeoutException as exc:
            raise OllamaError(f"Ollama timed out at {self.host}") from exc
        if r.status_code != 200:
            raise OllamaError(f"embed failed ({r.status_code}): {r.text}")
        data = r.json()
        embeddings = data.get("embeddings")
        if not embeddings:
            raise OllamaError(f"no embeddings in response: {data}")
        return list(embeddings[0])

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        """Single (non-streamed) /api/chat turn.

        Returns the raw response dict; the assistant message is `response["message"]`
        and may include `tool_calls`.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        if options:
            payload["options"] = options
        if format:
            payload["format"] = format
        try:
            r = await self._client.post(f"{self.host}/api/chat", json=payload)
        except httpx.ConnectError as exc:
            raise OllamaError(f"Ollama not reachable at {self.host}") from exc
        except httpx.TimeoutException as exc:
            raise OllamaError(f"Ollama timed out at {self.host}") from exc
        if r.status_code != 200:
            raise OllamaError(f"chat failed ({r.status_code}): {r.text}")
        return r.json()
