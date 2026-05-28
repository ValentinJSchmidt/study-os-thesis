from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chair import ChairDocumentKind


class ChairDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: ChairDocumentKind
    title: str | None
    content: str
    arxiv_id: str | None
    published_year: int | None
    created_at: datetime


class ChairOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    short_description: str
    professor_name: str
    professor_user_id: int | None
    website_url: str | None
    created_at: datetime
    documents: list[ChairDocumentOut] = []


class ChairCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    short_description: str = Field(min_length=10)
    professor_name: str = Field(min_length=2, max_length=255)
    professor_user_id: int | None = None
    website_url: str | None = Field(default=None, max_length=500)


class ChairPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    short_description: str | None = Field(default=None, min_length=10)
    professor_name: str | None = Field(default=None, min_length=2, max_length=255)
    professor_user_id: int | None = None
    website_url: str | None = Field(default=None, max_length=500)


class ArxivIngestRequest(BaseModel):
    """Request body to ingest a single ArXiv paper into a chair's document store."""

    arxiv_id: str = Field(
        min_length=5,
        max_length=50,
        description="ArXiv paper ID, e.g. '2301.07041' or 'cs/0301027'.",
    )
