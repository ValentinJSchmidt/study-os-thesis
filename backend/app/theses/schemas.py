from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import ThesisDifficulty, ThesisSource


class SkillsRequired(BaseModel):
    """Structured skills needed for a thesis proposal."""

    programming: list[str] = []
    math: list[str] = []
    theory: list[str] = []
    domain: list[str] = []
    other: list[str] = []


class GeneratedProposalItem(BaseModel):
    """One proposal as returned by the LLM during agent generation."""

    title: str = Field(min_length=3, max_length=500)
    abstract: str = Field(min_length=10, max_length=5000)
    difficulty: ThesisDifficulty = ThesisDifficulty.master
    skills_required: SkillsRequired = Field(default_factory=SkillsRequired)


class ThesisCreate(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    abstract: str = Field(min_length=10, max_length=10000)
    chair_id: int | None = None
    supervisor_id: int | None = None


class ThesisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    abstract: str
    chair_id: int | None
    supervisor_id: int | None
    submitter_id: int
    source: ThesisSource
    difficulty: ThesisDifficulty | None
    skills_required: dict[str, Any] | None
    generated_for_user_id: int | None
    chat_session_id: int | None
    created_at: datetime
