from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ThesisSource


class ThesisCreate(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    abstract: str = Field(min_length=10)
    supervisor_id: int | None = None


class ThesisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    abstract: str
    supervisor_id: int | None
    submitter_id: int
    source: ThesisSource
    created_at: datetime
