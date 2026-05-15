"""Tool-calling chat loop on top of Ollama.

The single registered tool is `search_theses` which performs pgvector retrieval
on the local thesis database.
"""
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm.ollama_client import OllamaClient
from app.models import ChatMessage, MessageRole
from app.tools.search_theses import search_theses

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


def _db_row_to_ollama_message(row: ChatMessage) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": row.role.value, "content": row.content or ""}
    if row.role == MessageRole.assistant and row.tool_calls:
        msg["tool_calls"] = row.tool_calls
    if row.role == MessageRole.tool and row.tool_name:
        msg["name"] = row.tool_name
    return msg


async def _execute_tool_call(
    session: AsyncSession, name: str, arguments: dict[str, Any] | str
) -> str:
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}
    if name != "search_theses":
        return json.dumps({"error": f"unknown tool: {name}"})
    query = str(arguments.get("query", "")).strip()
    k = int(arguments.get("k", 5))
    if not query:
        return json.dumps({"error": "query is required"})
    hits = await search_theses(session, query, k=k)
    return json.dumps({"results": hits})


async def run_agent_turn(
    session: AsyncSession,
    chat_session_id: int,
    user_content: str,
) -> list[ChatMessage]:
    """Persist the user message, run the tool-calling loop, persist results.

    Returns the list of newly created messages (user, any tool messages, final assistant).
    """
    settings = get_settings()
    client = OllamaClient()

    history_rows = list(
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
    )

    new_messages: list[ChatMessage] = []

    user_row = ChatMessage(
        session_id=chat_session_id, role=MessageRole.user, content=user_content
    )
    session.add(user_row)
    await session.flush()
    new_messages.append(user_row)

    ollama_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for row in history_rows:
        ollama_messages.append(_db_row_to_ollama_message(row))
    ollama_messages.append({"role": "user", "content": user_content})

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.chat(
            model=settings.ollama_chat_model,
            messages=ollama_messages,
            tools=TOOLS_SPEC,
        )
        assistant_msg = response.get("message", {}) or {}
        content = assistant_msg.get("content", "") or ""
        tool_calls = assistant_msg.get("tool_calls") or []

        if tool_calls:
            assistant_row = ChatMessage(
                session_id=chat_session_id,
                role=MessageRole.assistant,
                content=content,
                tool_calls=tool_calls,
            )
            session.add(assistant_row)
            await session.flush()
            new_messages.append(assistant_row)
            ollama_messages.append(
                {"role": "assistant", "content": content, "tool_calls": tool_calls}
            )

            for call in tool_calls:
                fn = call.get("function", {}) or {}
                name = fn.get("name", "")
                args = fn.get("arguments", {})
                tool_result = await _execute_tool_call(session, name, args)
                tool_row = ChatMessage(
                    session_id=chat_session_id,
                    role=MessageRole.tool,
                    content=tool_result,
                    tool_name=name,
                )
                session.add(tool_row)
                await session.flush()
                new_messages.append(tool_row)
                ollama_messages.append({"role": "tool", "content": tool_result, "name": name})
            continue

        assistant_row = ChatMessage(
            session_id=chat_session_id,
            role=MessageRole.assistant,
            content=content,
        )
        session.add(assistant_row)
        await session.flush()
        new_messages.append(assistant_row)
        break
    else:
        assistant_row = ChatMessage(
            session_id=chat_session_id,
            role=MessageRole.assistant,
            content="(stopped: tool-call iteration limit reached)",
        )
        session.add(assistant_row)
        await session.flush()
        new_messages.append(assistant_row)

    await session.commit()
    for row in new_messages:
        await session.refresh(row)
    return new_messages
