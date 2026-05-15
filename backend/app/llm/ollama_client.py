from typing import Any

import httpx

from app.config import get_settings


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, host: str | None = None, timeout: float = 600.0):
        s = get_settings()
        self.host = (host or s.ollama_host).rstrip("/")
        self.timeout = timeout

    async def embed(self, model: str, text: str) -> list[float]:
        """Return one embedding vector for `text` using Ollama's /api/embed."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.host}/api/embed",
                json={"model": model, "input": text},
            )
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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.host}/api/chat", json=payload)
        if r.status_code != 200:
            raise OllamaError(f"chat failed ({r.status_code}): {r.text}")
        return r.json()
