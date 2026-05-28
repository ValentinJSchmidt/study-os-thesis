"""LLM provider port (interface) for the port-adapter pattern.

All application code that needs to call an LLM depends on this Protocol, never
on a concrete provider implementation.  Provider adapters (OllamaClient,
LiteLLMAdapter, …) satisfy this protocol structurally — no inheritance required.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    """Combined chat + embedding port for LLM providers.

    Any concrete class that implements ``chat``, ``embed``, and ``aclose``
    with the correct signatures satisfies this protocol.
    """

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a single (non-streamed) chat turn.

        Returns a dict in Ollama's response shape::

            {
                "message": {
                    "role": "assistant",
                    "content": "...",
                    "tool_calls": [...]   # optional
                }
            }

        All provider adapters normalise their provider-specific response format
        to this shape so that service-layer code remains provider-agnostic.
        """
        ...

    async def embed(self, model: str, text: str) -> list[float]:
        """Return one embedding vector for *text* using *model*."""
        ...

    async def aclose(self) -> None:
        """Release any held resources (HTTP connection pools, etc.)."""
        ...
