"""Business logic for chat sessions and the LLM agent loop."""

import json
from typing import Any

from app.config import Settings
from app.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.llm.ollama_client import OllamaClient
from app.models import ChatMessage, ChatSession, MessageRole
from app.repositories.chat_repository import ChatRepository
from app.tools.search_theses import search_theses_with_client

SYSTEM_PROMPT = (
    "You are an assistant helping a student pick a thesis topic. "
    "You have access to a tool `search_theses(query, k)` that retrieves theses "
    "from a local database ranked by semantic similarity. "
    "Use it whenever the student expresses interests, methods, fields, or asks "
    "what is available. Prefer concise queries that capture the essential keywords. "
    "When you recommend theses, cite each one by its id and explain in one sentence "
    "why it might fit. If retrieval returns nothing relevant, say so honestly and "
    "ask a clarifying question."
)

TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_theses",
            "description": (
                "Semantic search over the local thesis database. "
                "Returns up to k theses ranked by cosine similarity to the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free-text search query (topics, methods, fields).",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (1-20).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    }
]

MAX_TOOL_ITERATIONS = 4
# Keep only the most recent N messages sent to Ollama to avoid exceeding the
# model's context window and to bound memory/latency for long conversations.
MAX_HISTORY_MESSAGES = 20


def _db_row_to_ollama_message(row: ChatMessage) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": row.role.value, "content": row.content or ""}
    if row.role == MessageRole.assistant and row.tool_calls:
        msg["tool_calls"] = row.tool_calls
    if row.role == MessageRole.tool and row.tool_name:
        msg["name"] = row.tool_name
    return msg


class ChatService:
    """Business logic for chat sessions and messages."""

    def __init__(
        self,
        chat_repo: ChatRepository,
        ollama_client: OllamaClient,
        settings: Settings,
    ) -> None:
        self._chat_repo = chat_repo
        self._ollama = ollama_client
        self._settings = settings

    async def create_session(self, user_id: int) -> ChatSession:
        return await self._chat_repo.create_session(user_id)

    async def list_sessions(self, user_id: int) -> list[ChatSession]:
        return await self._chat_repo.list_sessions(user_id)

    async def get_messages(self, session_id: int, user_id: int) -> list[ChatMessage]:
        chat = await self._chat_repo.get_session(session_id)
        if not chat:
            raise NotFoundException("Session", session_id)
        if chat.user_id != user_id:
            raise ForbiddenException("You do not own this session")
        return await self._chat_repo.list_messages(session_id)

    async def send_message(
        self, session_id: int, user_id: int, content: str
    ) -> list[ChatMessage]:
        content = content.strip()
        if not content:
            raise BadRequestException("Empty message")

        chat = await self._chat_repo.get_session(session_id)
        if not chat:
            raise NotFoundException("Session", session_id)
        if chat.user_id != user_id:
            raise ForbiddenException("You do not own this session")

        return await self._run_agent_turn(session_id, content)

    # ---- Agent loop (moved from app/llm/agent.py) ----

    async def _run_agent_turn(
        self, chat_session_id: int, user_content: str
    ) -> list[ChatMessage]:
        history = await self._chat_repo.list_messages(chat_session_id)
        # Truncate history to avoid exceeding the model's context window.
        history = history[-MAX_HISTORY_MESSAGES:]

        new_messages: list[ChatMessage] = []

        user_row = await self._chat_repo.create_message(
            session_id=chat_session_id,
            role=MessageRole.user,
            content=user_content,
            flush_only=True,
        )
        new_messages.append(user_row)

        ollama_messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        for row in history:
            ollama_messages.append(_db_row_to_ollama_message(row))
        ollama_messages.append({"role": "user", "content": user_content})

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await self._ollama.chat(
                model=self._settings.ollama_chat_model,
                messages=ollama_messages,
                tools=TOOLS_SPEC,
            )
            assistant_msg = response.get("message", {}) or {}
            assistant_content = assistant_msg.get("content", "") or ""
            tool_calls = assistant_msg.get("tool_calls") or []

            if tool_calls:
                assistant_row = await self._chat_repo.create_message(
                    session_id=chat_session_id,
                    role=MessageRole.assistant,
                    content=assistant_content,
                    tool_calls=tool_calls,
                    flush_only=True,
                )
                new_messages.append(assistant_row)
                ollama_messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_content,
                        "tool_calls": tool_calls,
                    }
                )

                for call in tool_calls:
                    fn = call.get("function", {}) or {}
                    name = fn.get("name", "")
                    args = fn.get("arguments", {})
                    tool_result = await self._execute_tool_call(name, args)
                    tool_row = await self._chat_repo.create_message(
                        session_id=chat_session_id,
                        role=MessageRole.tool,
                        content=tool_result,
                        tool_name=name,
                        flush_only=True,
                    )
                    new_messages.append(tool_row)
                    ollama_messages.append(
                        {"role": "tool", "content": tool_result, "name": name}
                    )
                continue

            assistant_row = await self._chat_repo.create_message(
                session_id=chat_session_id,
                role=MessageRole.assistant,
                content=assistant_content,
                flush_only=True,
            )
            new_messages.append(assistant_row)
            break
        else:
            assistant_row = await self._chat_repo.create_message(
                session_id=chat_session_id,
                role=MessageRole.assistant,
                content="(stopped: tool-call iteration limit reached)",
                flush_only=True,
            )
            new_messages.append(assistant_row)

        await self._chat_repo.commit()
        for row in new_messages:
            await self._chat_repo.refresh(row)
        return new_messages

    async def _execute_tool_call(
        self, name: str, arguments: dict[str, Any] | str
    ) -> str:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        if name != "search_theses":
            return json.dumps({"error": f"unknown tool: {name}"})
        query = str(arguments.get("query", "")).strip()
        try:
            k = max(1, min(20, int(arguments.get("k", 5))))
        except (TypeError, ValueError):
            k = 5
        if not query:
            return json.dumps({"error": "query is required"})
        hits = await search_theses_with_client(
            self._ollama, self._settings, query, k=k
        )
        return json.dumps({"results": hits})
