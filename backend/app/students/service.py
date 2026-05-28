"""Business logic for student profiles and transcript processing."""

import json
import logging
from typing import Any

from app.config import Settings
from app.exceptions import BadRequestException, NotFoundException
from app.llm.port import LLMPort
from app.models.student import Student
from app.students.repository import StudentRepository
from app.students.schemas import StudentCourseItem, TranscriptParseResult

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM prompt for transcript extraction
# ---------------------------------------------------------------------------

_TRANSCRIPT_PROMPT = """You are a data-extraction assistant. You will receive the raw text of a German university transcript of records (Notenauszug / Leistungsübersicht).

Extract ALL course rows and return a single JSON object with this exact schema:
{
  "gpa": <credit-weighted average German grade as float, lower is better, null if not computable>,
  "courses": [
    {
      "course_name": "<full course name only, no IDs or other metadata>",
      "credits": <ECTS credits as float or null>,
      "grade": "<ONLY the grade value as string, e.g. '1,3' or '2,0' or 'bestanden' or null — never a course ID or other text>",
      "semester_taken": "<e.g. 'WS 2023/24' or null>"
    }
  ]
}

Rules:
- Include every course row, including failed ones.
- "course_name" must contain ONLY the human-readable course name (e.g. "Self-Driving Cars"), never IDs, codes, or metadata.
- "grade" must contain ONLY the grade value (e.g. "1,3", "2,0", "bestanden", "nicht bestanden"). Never put a course ID, semester string, or any other text in the grade field.
- Preserve the original grade string (comma decimal: '1,3' not '1.3').
- If a course has no numeric grade (e.g. "bestanden"), keep it as-is.
- Omit any extra fields not listed in the schema above (e.g. course_id, credits_weight_value).
- Compute gpa as sum(grade * credits) / sum(credits) for all rows with a parseable numeric grade. Use period decimal for the float result.
- Do NOT include any explanation or markdown. Output ONLY the raw JSON object.

Tables from the PDF have been pre-formatted as Markdown tables. Non-table content appears as plain text. Pages are separated by "---".

Transcript text:
"""


def _compute_gpa(courses: list[StudentCourseItem]) -> float | None:
    """Credit-weighted average of German numeric grades. Lower is better."""
    total_credits = 0.0
    weighted_sum = 0.0
    for c in courses:
        if c.grade is None or c.credits is None:
            continue
        grade_str = c.grade.replace(",", ".")
        try:
            grade_val = float(grade_str)
        except ValueError:
            continue
        if not (1.0 <= grade_val <= 5.0):
            continue
        weighted_sum += grade_val * float(c.credits)
        total_credits += float(c.credits)
    if total_credits == 0:
        return None
    return round(weighted_sum / total_credits, 2)


class StudentService:
    def __init__(
        self,
        student_repo: StudentRepository,
        chat_client: LLMPort,
        embed_client: LLMPort,
        settings: Settings,
    ) -> None:
        self._student_repo = student_repo
        self._ollama = chat_client
        self._embed = embed_client
        self._settings = settings

    async def get_profile(self, user_id: int) -> Student:
        student = await self._student_repo.get_by_user_id(user_id)
        if student is None:
            raise NotFoundException("Student profile", user_id)
        return student

    async def upload_transcript(
        self,
        user_id: int,
        pdf_bytes: bytes,
        program: str | None = None,
        semester: int | None = None,
    ) -> Student:
        _logger.info(
            "Transcript upload started: user_id=%d size=%d bytes program=%r semester=%r",
            user_id,
            len(pdf_bytes),
            program,
            semester,
        )

        _logger.info("Step 1/5 — Extracting text from PDF (user_id=%d)", user_id)
        raw_text = await _extract_pdf_text(pdf_bytes)
        if not raw_text.strip():
            raise BadRequestException("Could not extract text from the uploaded PDF. Make sure it is not a scanned image.")
        _logger.info("Step 1/5 — PDF text extracted: %d characters (user_id=%d)", len(raw_text), user_id)

        _logger.info(
            "Step 2/5 — Sending transcript to LLM for structured extraction (model=%s user_id=%d)",
            self._settings.effective_extract_model,
            user_id,
        )
        parse_result = await self._parse_transcript_with_llm(raw_text)
        _logger.info("Step 2/5 — LLM extraction complete: %d courses parsed (user_id=%d)", len(parse_result.courses), user_id)

        gpa = _compute_gpa(parse_result.courses)
        _logger.info("Step 3/5 — GPA computed: %s (user_id=%d)", gpa, user_id)

        _logger.info(
            "Step 4/5 — Creating course profile embedding (model=%s user_id=%d)",
            self._settings.ollama_embed_model,
            user_id,
        )
        profile_embedding = await self._embed_course_profile(parse_result.courses)
        if profile_embedding is not None:
            _logger.info("Step 4/5 — Embedding created: dim=%d (user_id=%d)", len(profile_embedding), user_id)
        else:
            _logger.warning("Step 4/5 — Embedding skipped (user_id=%d)", user_id)

        _logger.info(
            "Step 5/5 — Persisting student profile and %d courses (user_id=%d)",
            len(parse_result.courses),
            user_id,
        )
        student = await self._student_repo.upsert(
            user_id,
            gpa=gpa,
            program=program,
            semester=semester,
            profile_embedding=profile_embedding,
            courses=parse_result.courses,
        )
        await self._student_repo.commit()
        _logger.info("Step 5/5 — Student profile committed to DB (user_id=%d)", user_id)

        student = await self._student_repo.get_by_user_id(user_id)
        _logger.info("Transcript upload complete (user_id=%d)", user_id)
        return student  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _parse_transcript_with_llm(self, raw_text: str) -> TranscriptParseResult:
        prompt = _TRANSCRIPT_PROMPT + raw_text
        try:
            response = await self._ollama.chat(
                model=self._settings.effective_extract_model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
        except Exception as exc:
            _logger.error("LLM transcript extraction failed: %s", exc)
            raise BadRequestException(f"Transcript extraction failed: {exc}") from exc
        content: str = (response.get("message", {}) or {}).get("content", "") or ""
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        try:
            data: Any = json.loads(content)
        except json.JSONDecodeError as exc:
            _logger.error("LLM returned non-JSON transcript parse result: %s", content[:500])
            raise BadRequestException("The LLM could not parse the transcript into structured data. Please ensure the PDF is a valid text-based transcript.") from exc
        try:
            return TranscriptParseResult.model_validate(data)
        except Exception as exc:
            _logger.warning(
                "Strict validation failed (%s), attempting per-course fallback: %s",
                exc,
                data,
            )
        # Fallback: validate each course individually, skip invalid ones
        valid_courses: list[StudentCourseItem] = []
        raw_courses = data.get("courses", []) if isinstance(data, dict) else []
        for raw in raw_courses:
            try:
                valid_courses.append(StudentCourseItem.model_validate(raw))
            except Exception as course_exc:
                _logger.warning("Skipping invalid course row (%s): %s", course_exc, raw)
        if not valid_courses:
            _logger.error("No valid courses could be extracted from: %s", data)
            raise BadRequestException("The LLM could not produce any valid course rows from the transcript.")
        gpa_raw = data.get("gpa") if isinstance(data, dict) else None
        try:
            gpa_val = float(gpa_raw) if gpa_raw is not None else None
        except (TypeError, ValueError):
            gpa_val = None
        return TranscriptParseResult(gpa=gpa_val, courses=valid_courses)

    async def _embed_course_profile(self, courses: list[StudentCourseItem]) -> list[float] | None:
        if not courses:
            _logger.warning("No courses to embed — profile_embedding will be null.")
            return None
        parts = [f"{c.course_name} ({c.credits} ECTS)" if c.credits else c.course_name for c in courses]
        text = "; ".join(parts)
        _logger.info("Embedding course profile: %d courses, %d chars of text", len(courses), len(text))
        try:
            vec = await self._embed.embed(self._settings.ollama_embed_model, text)
            _logger.info("Course profile embedding done: dim=%d", len(vec))
            return vec
        except Exception as exc:
            _logger.warning("Failed to embed course profile; profile_embedding will be null. Reason: %s", exc)
            return None


async def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF using pdfplumber.

    Tables are rendered as Markdown tables; remaining text is appended as-is.
    Pages are separated by a horizontal rule so the LLM has clear page boundaries.
    Runs synchronously in a thread pool to avoid blocking the async event loop.
    """
    import asyncio
    import io

    _logger = logging.getLogger(__name__)

    def _cell(c: str | None) -> str:
        return (c or "").replace("\n", " ").strip()

    def _sync_extract(data: bytes) -> str:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("pdfplumber is not installed. Add it to pyproject.toml: pdfplumber>=0.11") from exc

        pages_text: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            _logger.info("PDF has %d page(s)", len(pdf.pages))
            for page in pdf.pages:
                parts: list[str] = []
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    header, *rows = table
                    md: list[str] = [
                        "| " + " | ".join(_cell(c) for c in header) + " |",
                        "| " + " | ".join("---" for _ in header) + " |",
                    ]
                    for row in rows:
                        md.append("| " + " | ".join(_cell(c) for c in row) + " |")
                    parts.append("\n".join(md))
                plain = page.extract_text() or ""
                if plain.strip():
                    parts.append(plain)
                pages_text.append("\n\n".join(parts))

        total_chars = sum(len(p) for p in pages_text)
        _logger.info("PDF extracted: %d pages, %d total characters", len(pages_text), total_chars)
        return "\n\n---\n\n".join(pages_text)

    return await asyncio.get_event_loop().run_in_executor(None, _sync_extract, pdf_bytes)
