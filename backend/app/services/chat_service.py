"""Business logic for chat sessions and the LLM agent loop."""

import json
import logging
from typing import Any

from app.config import Settings
from app.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.llm.ollama_client import OllamaClient
from app.models import ChatMessage, ChatSession, MessageRole, Thesis, ThesisSource
from app.repositories.chair_repository import ChairRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.thesis_repository import ThesisRepository
from app.schemas.thesis import GeneratedProposalItem
from app.tools.search_theses import search_theses_with_client

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert academic advisor helping a student at a German university find \
a thesis topic that fits their academic background.

You have access to three tools:
- `search_chairs(query, k)` — finds research chairs whose focus areas match the query.
- `search_theses(query, k, chair_id)` — finds open thesis proposals, optionally filtered by chair.
- `generate_proposal(chair_id, research_direction, count)` — generates 1-3 personalized \
  thesis proposals for the student based on a specific chair and research direction. \
  ONLY call this when the student explicitly asks you to generate or create a proposal.

## Recommended workflow
1. The student's course profile will be injected into this conversation as context.
2. Use `search_chairs` with a query derived from the student's strongest or most \
   relevant courses to find fitting chairs.
3. For each promising chair, use `search_theses` with `chair_id` to find open proposals.
4. Synthesise a personalised recommendation: explain which chair fits the student's \
   background and why, then list the most relevant thesis proposals with their ids.
5. If the student explicitly asks to generate a proposal, call `generate_proposal` with \
   the most fitting chair_id, a specific research_direction derived from their courses \
   and the chair's focus, and count=1-3. The tool will infer difficulty from the student's \
   GPA, semester, and the research complexity.
6. After generating, tell the student which proposals were saved (cite their ids and titles) \
   and that they can find them under "Meine Vorschläge".

Always cite thesis ids and chair names in your recommendations.\
"""

_PROPOSAL_GENERATION_PROMPT = """\
You are a research proposal writer for a German university. Generate {count} distinct \
thesis proposal(s) for a student based on the information below.

## Chair
Name: {chair_name}
Description: {chair_description}

## Student profile
GPA (German scale, lower=better): {gpa}
Semester: {semester}
Program: {program}
Courses: {courses}

## Requested research direction
{research_direction}

## Instructions
- Each proposal must be a concrete, feasible Master's or Bachelor's thesis.
- Infer the difficulty (bachelor/master/phd) from the student's GPA, semester, and the \
  complexity of the research direction. Lower GPA (e.g. 1.x) + higher semester → more \
  advanced difficulty.
- For skills_required, list specific tools/languages/concepts the student would need.
- Return ONLY a valid JSON array, no markdown, no explanation.

## Required JSON format
[
  {{
    "title": "<concise thesis title>",
    "abstract": "<2-4 sentence description of the research question, method, and expected contribution>",
    "difficulty": "bachelor" | "master" | "phd",
    "skills_required": {{
      "programming": ["Python", "PyTorch"],
      "math": ["Linear Algebra", "Probability Theory"],
      "theory": ["Deep Learning", "Optimization"],
      "domain": ["Computer Vision", "Robotics"],
      "other": []
    }}
  }}
]
"""

TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_chairs",
            "description": (
                "Semantic search over research chair descriptions and paper abstracts. "
                "Returns chairs whose research focus best matches the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free-text query derived from student interests or courses.",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (1-10).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_theses",
            "description": (
                "Semantic + keyword search over open thesis proposals. "
                "Optionally filter by chair_id to scope results to a specific chair."
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
                    "chair_id": {
                        "type": "integer",
                        "description": "If provided, restrict results to this chair's proposals.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_proposal",
            "description": (
                "Generate 1-3 personalized thesis proposals for the student based on a "
                "specific chair and research direction. Only call this when the student "
                "explicitly asks to generate or create a proposal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "chair_id": {
                        "type": "integer",
                        "description": "The id of the target research chair.",
                    },
                    "research_direction": {
                        "type": "string",
                        "description": (
                            "Specific topic or research direction to explore, derived "
                            "from the student's courses and the chair's focus."
                        ),
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of proposals to generate (1-3).",
                        "default": 1,
                    },
                },
                "required": ["chair_id", "research_direction"],
            },
        },
    },
]

MAX_TOOL_ITERATIONS = 6
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
        student_repo: StudentRepository | None = None,
        chair_repo: ChairRepository | None = None,
        thesis_repo: ThesisRepository | None = None,
    ) -> None:
        self._chat_repo = chat_repo
        self._ollama = ollama_client
        self._settings = settings
        self._student_repo = student_repo
        self._chair_repo = chair_repo
        self._thesis_repo = thesis_repo

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

    async def _build_student_context(self, user_id: int) -> str | None:
        """Return a short text summary of the student's course profile, or None."""
        if self._student_repo is None:
            return None
        try:
            student = await self._student_repo.get_by_user_id(user_id)
            if student is None or not student.courses:
                return None
            lines = [f"## Student academic profile (GPA: {student.gpa or 'N/A'})"]
            if student.program:
                lines.append(f"Program: {student.program}, Semester: {student.semester or 'N/A'}")
            lines.append("Completed courses:")
            for c in student.courses:
                grade_str = f", grade {c.grade}" if c.grade else ""
                credits_str = f" ({c.credits} ECTS)" if c.credits else ""
                lines.append(f"  - {c.course_name}{credits_str}{grade_str}")
            return "\n".join(lines)
        except Exception as exc:
            _logger.warning("Could not load student profile for chat context: %s", exc)
            return None

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

        return await self._run_agent_turn(session_id, content, user_id)

    # ---- Agent loop (moved from app/llm/agent.py) ----

    async def _run_agent_turn(
        self, chat_session_id: int, user_content: str, user_id: int
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

        # Build system prompt, injecting student profile if available.
        student_context = await self._build_student_context(user_id)
        system_content = SYSTEM_PROMPT
        if student_context:
            system_content = system_content + "\n\n" + student_context

        ollama_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_content}
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
                    tool_result = await self._execute_tool_call(
                        name, args, user_id=user_id, chat_session_id=chat_session_id
                    )
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
        self,
        name: str,
        arguments: dict[str, Any] | str,
        *,
        user_id: int,
        chat_session_id: int,
    ) -> str:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        if name == "search_theses":
            return await self._tool_search_theses(arguments)
        elif name == "search_chairs":
            return await self._tool_search_chairs(arguments)
        elif name == "generate_proposal":
            return await self._tool_generate_proposal(
                arguments, user_id=user_id, chat_session_id=chat_session_id
            )
        else:
            return json.dumps({"error": f"unknown tool: {name}"})

    async def _tool_search_theses(self, arguments: dict[str, Any]) -> str:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return json.dumps({"error": "query is required"})
        try:
            k = max(1, min(20, int(arguments.get("k", 5))))
        except (TypeError, ValueError):
            k = 5
        chair_id: int | None = None
        raw_chair = arguments.get("chair_id")
        if raw_chair is not None:
            try:
                chair_id = int(raw_chair)
            except (TypeError, ValueError):
                pass
        hits = await search_theses_with_client(
            self._ollama, self._settings, query, k=k, chair_id=chair_id
        )
        return json.dumps({"results": hits})

    async def _tool_search_chairs(self, arguments: dict[str, Any]) -> str:
        if self._chair_repo is None:
            return json.dumps({"error": "chair search not available"})
        query = str(arguments.get("query", "")).strip()
        if not query:
            return json.dumps({"error": "query is required"})
        try:
            k = max(1, min(10, int(arguments.get("k", 5))))
        except (TypeError, ValueError):
            k = 5
        try:
            embedding = await self._ollama.embed(self._settings.ollama_embed_model, query)
        except Exception as exc:
            _logger.warning("Could not embed chair search query: %s", exc)
            return json.dumps({"error": "embedding service unavailable"})
        results = await self._chair_repo.search_by_embedding(embedding, k=k)
        return json.dumps({"results": results})

    async def _tool_generate_proposal(
        self,
        arguments: dict[str, Any],
        *,
        user_id: int,
        chat_session_id: int,
    ) -> str:
        if self._chair_repo is None or self._thesis_repo is None:
            return json.dumps({"error": "proposal generation not available"})

        # -- Parse arguments --
        raw_chair = arguments.get("chair_id")
        if raw_chair is None:
            return json.dumps({"error": "chair_id is required"})
        try:
            chair_id = int(raw_chair)
        except (TypeError, ValueError):
            return json.dumps({"error": "chair_id must be an integer"})

        research_direction = str(arguments.get("research_direction", "")).strip()
        if not research_direction:
            return json.dumps({"error": "research_direction is required"})

        try:
            count = max(1, min(3, int(arguments.get("count", 1))))
        except (TypeError, ValueError):
            count = 1

        _logger.info(
            "generate_proposal: user_id=%d chair_id=%d count=%d direction=%r",
            user_id, chair_id, count, research_direction[:80],
        )

        # -- Load chair --
        chair = await self._chair_repo.get_by_id(chair_id, load_documents=False)
        if chair is None:
            return json.dumps({"error": f"Chair {chair_id} not found"})

        # -- Load student profile --
        gpa = "N/A"
        semester = "N/A"
        program = "N/A"
        courses_str = "No courses available"
        if self._student_repo is not None:
            try:
                student = await self._student_repo.get_by_user_id(user_id)
                if student:
                    gpa = str(student.gpa) if student.gpa is not None else "N/A"
                    semester = str(student.semester) if student.semester else "N/A"
                    program = student.program or "N/A"
                    if student.courses:
                        courses_str = "; ".join(
                            f"{c.course_name} ({c.credits} ECTS, {c.grade})"
                            if c.credits and c.grade
                            else c.course_name
                            for c in student.courses
                        )
            except Exception as exc:
                _logger.warning("Could not load student profile for proposal generation: %s", exc)

        # -- Call LLM to generate proposals --
        prompt = _PROPOSAL_GENERATION_PROMPT.format(
            count=count,
            chair_name=chair.name,
            chair_description=chair.short_description,
            gpa=gpa,
            semester=semester,
            program=program,
            courses=courses_str,
            research_direction=research_direction,
        )
        _logger.info("Calling LLM to generate %d proposal(s) for chair %d", count, chair_id)
        try:
            response = await self._ollama.chat(
                model=self._settings.effective_extract_model,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            _logger.error("LLM call failed during proposal generation: %s", exc)
            return json.dumps({"error": f"LLM unavailable: {exc}"})

        content = (response.get("message", {}) or {}).get("content", "") or ""
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        try:
            raw_list: Any = json.loads(content)
            if not isinstance(raw_list, list):
                raw_list = [raw_list]
            proposals = [GeneratedProposalItem.model_validate(p) for p in raw_list[:count]]
        except Exception as exc:
            _logger.error("Failed to parse LLM proposal output: %s\nContent: %s", exc, content[:500])
            return json.dumps({"error": "LLM returned invalid proposal format", "raw": content[:200]})

        # -- Persist each proposal --
        saved = []
        for proposal in proposals:
            _logger.info("Embedding proposal: %r", proposal.title)
            try:
                embedding = await self._ollama.embed(
                    self._settings.ollama_embed_model,
                    f"{proposal.title}\n\n{proposal.abstract}",
                )
            except Exception:
                embedding = None

            thesis = Thesis(
                title=proposal.title,
                abstract=proposal.abstract,
                chair_id=chair_id,
                submitter_id=user_id,
                source=ThesisSource.student,
                difficulty=proposal.difficulty,
                skills_required=proposal.skills_required.model_dump(),
                generated_for_user_id=user_id,
                chat_session_id=chat_session_id,
                embedding=embedding,
            )
            self._thesis_repo.session.add(thesis)
            await self._thesis_repo.session.flush()
            await self._thesis_repo.session.refresh(thesis)
            # Commit each proposal immediately so it's visible to GET /api/proposals/mine
            # even before the chat turn finishes.
            await self._thesis_repo.commit()
            saved.append({"id": thesis.id, "title": thesis.title, "difficulty": thesis.difficulty.value})
            _logger.info("Proposal saved: id=%d title=%r", thesis.id, thesis.title)

        _logger.info("Generated and saved %d proposal(s) for user_id=%d", len(saved), user_id)
        return json.dumps({
            "generated": len(saved),
            "proposals": saved,
            "message": f"{len(saved)} proposal(s) saved to 'Meine Vorschläge'.",
        })
