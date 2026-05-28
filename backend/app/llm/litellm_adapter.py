"""LiteLLM-based adapter that satisfies LLMPort.

LiteLLM provides a unified interface to 100+ LLM providers (Azure OpenAI,
DeepSeek, Ollama, OpenAI, Anthropic, …).  This adapter wraps
``litellm.acompletion`` and ``litellm.aembedding`` and normalises their
OpenAI-format responses into the Ollama dict shape that the service layer
already expects::

    {"message": {"role": "assistant", "content": "...", "tool_calls": [...]}}

Supported providers and their litellm model name prefixes
---------------------------------------------------------
- Ollama     : ``ollama_chat/<model>``   (e.g. ``ollama_chat/gemma4:26b``)
- Azure      : ``azure/<deployment>``    (e.g. ``azure/gpt-4o``)
- DeepSeek   : ``deepseek/<model>``      (e.g. ``deepseek/deepseek-chat``)

The factory (``app.llm.factory``) constructs instances of this class with the
correct model names and provider-specific kwargs.
"""

import logging
from typing import Any

import litellm

_logger = logging.getLogger(__name__)

# Suppress litellm's verbose internal logging by default.
litellm.suppress_debug_info = True


def _normalise_tool_calls(
    tool_calls: list[Any],
) -> list[dict[str, Any]]:
    """Convert LiteLLM/OpenAI tool_call objects to Ollama's dict shape.

    LiteLLM returns ``ChatCompletionMessageToolCall`` pydantic objects with:
        .function.name  (str)
        .function.arguments  (str — JSON encoded)

    Ollama returns plain dicts with:
        {"function": {"name": str, "arguments": dict}}

    We convert to the Ollama shape so the service layer is unaffected.
    """
    result: list[dict[str, Any]] = []
    for tc in tool_calls:
        try:
            fn = tc.function
            import json
            args: Any = fn.arguments
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            result.append(
                {
                    "function": {
                        "name": fn.name,
                        "arguments": args,
                    }
                }
            )
        except Exception as exc:
            _logger.warning("Could not normalise tool call %r: %s", tc, exc)
    return result


class LiteLLMAdapter:
    """Provider-agnostic LLM adapter built on top of LiteLLM.

    Parameters
    ----------
    chat_model:
        The fully-qualified litellm model string used for ``chat()`` calls.
        Examples: ``"ollama_chat/gemma4:26b"``, ``"azure/gpt-4o"``,
        ``"deepseek/deepseek-chat"``.
    embed_model:
        The fully-qualified litellm model string used for ``embed()`` calls.
        Examples: ``"ollama/qwen3-embedding:4b"``,
        ``"azure/text-embedding-3-small"``.
    **kwargs:
        Extra kwargs forwarded to every litellm call (``api_base``,
        ``api_key``, ``api_version``, …).  Provider-specific kwargs can be
        split via ``chat_kwargs`` / ``embed_kwargs`` if they differ between
        the two operations.
    chat_kwargs:
        Additional kwargs forwarded only to ``acompletion`` calls.
    embed_kwargs:
        Additional kwargs forwarded only to ``aembedding`` calls.
    """

    def __init__(
        self,
        chat_model: str,
        embed_model: str,
        chat_kwargs: dict[str, Any] | None = None,
        embed_kwargs: dict[str, Any] | None = None,
        **shared_kwargs: Any,
    ) -> None:
        self._chat_model = chat_model
        self._embed_model = embed_model
        self._chat_kwargs: dict[str, Any] = {**shared_kwargs, **(chat_kwargs or {})}
        self._embed_kwargs: dict[str, Any] = {**shared_kwargs, **(embed_kwargs or {})}

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a single non-streamed chat turn via LiteLLM.

        The *model* parameter mirrors the OllamaClient signature (the caller
        passes the configured model name).  We use ``self._chat_model``
        internally so that the provider prefix is always correct regardless of
        what the caller passes in — this keeps Settings usage identical to the
        Ollama path.
        """
        kwargs: dict[str, Any] = dict(self._chat_kwargs)
        if tools:
            kwargs["tools"] = tools
        # Map Ollama-style options (num_predict, temperature, …) to OpenAI params.
        if options:
            if "temperature" in options:
                kwargs["temperature"] = options["temperature"]
            if "num_predict" in options:
                kwargs["max_tokens"] = options["num_predict"]

        response = await litellm.acompletion(
            model=self._chat_model,
            messages=messages,
            stream=False,
            **kwargs,
        )

        # Normalise OpenAI ModelResponse → Ollama dict shape.
        msg = response.choices[0].message
        result: dict[str, Any] = {
            "role": msg.role or "assistant",
            "content": msg.content or "",
        }
        if msg.tool_calls:
            result["tool_calls"] = _normalise_tool_calls(msg.tool_calls)

        return {"message": result}

    async def embed(self, model: str, text: str) -> list[float]:
        """Return one embedding vector for *text* via LiteLLM.

        Like ``chat()``, the *model* parameter is accepted for API compatibility
        but the adapter uses ``self._embed_model`` to ensure the correct provider
        prefix.
        """
        response = await litellm.aembedding(
            model=self._embed_model,
            input=[text],
            **self._embed_kwargs,
        )
        return list(response.data[0]["embedding"])

    async def aclose(self) -> None:
        """No-op — LiteLLM manages its own connection lifecycle."""
        pass
