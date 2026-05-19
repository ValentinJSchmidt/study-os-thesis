from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Thesis, ThesisSource


class ThesisRepository:
    """Data-access layer for the `theses` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create(
        self,
        title: str,
        abstract: str,
        submitter_id: int,
        source: ThesisSource,
        supervisor_id: int | None = None,
        chair_id: int | None = None,
        embedding: list[float] | None = None,
    ) -> Thesis:
        thesis = Thesis(
            title=title,
            abstract=abstract,
            submitter_id=submitter_id,
            source=source,
            supervisor_id=supervisor_id,
            chair_id=chair_id,
            embedding=embedding,
        )
        self._session.add(thesis)
        await self._session.flush()
        await self._session.refresh(thesis)
        return thesis

    async def list(self, limit: int = 20, offset: int = 0) -> list[Thesis]:
        rows = await self._session.scalars(
            select(Thesis).order_by(Thesis.created_at.desc()).limit(limit).offset(offset)
        )
        return list(rows)

    async def commit(self) -> None:
        await self._session.commit()

    async def get_by_id(self, thesis_id: int) -> Thesis | None:
        return await self._session.get(Thesis, thesis_id)

    async def list_for_user(self, user_id: int) -> list[Thesis]:
        """Return all proposals generated for a specific student, newest first."""
        rows = await self._session.scalars(
            select(Thesis)
            .where(Thesis.generated_for_user_id == user_id)
            .order_by(Thesis.created_at.desc())
        )
        return list(rows)
