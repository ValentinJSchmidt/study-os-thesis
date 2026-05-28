from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chair import Chair, ChairDocument, ChairDocumentKind


class ChairRepository:
    """Data-access layer for the `chairs` and `chair_documents` tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Chair CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        name: str,
        short_description: str,
        professor_name: str,
        professor_user_id: int | None,
        website_url: str | None,
    ) -> Chair:
        chair = Chair(
            name=name,
            short_description=short_description,
            professor_name=professor_name,
            professor_user_id=professor_user_id,
            website_url=website_url,
        )
        self._session.add(chair)
        await self._session.flush()
        await self._session.refresh(chair)
        return chair

    async def get_by_id(self, chair_id: int, *, load_documents: bool = False) -> Chair | None:
        stmt = select(Chair).where(Chair.id == chair_id)
        if load_documents:
            stmt = stmt.options(selectinload(Chair.documents))
        return await self._session.scalar(stmt)

    async def list(self, limit: int = 100, offset: int = 0) -> list[Chair]:
        rows = await self._session.scalars(
            select(Chair)
            .options(selectinload(Chair.documents))
            .order_by(Chair.name)
            .limit(limit)
            .offset(offset)
        )
        return list(rows)

    async def update(self, chair: Chair, **fields: object) -> Chair:
        for key, value in fields.items():
            setattr(chair, key, value)
        await self._session.flush()
        await self._session.refresh(chair)
        return chair

    async def delete(self, chair: Chair) -> None:
        await self._session.delete(chair)
        await self._session.flush()

    # ------------------------------------------------------------------
    # ChairDocument operations
    # ------------------------------------------------------------------

    async def get_document(self, doc_id: int) -> ChairDocument | None:
        return await self._session.get(ChairDocument, doc_id)

    async def get_document_by_arxiv(
        self, chair_id: int, arxiv_id: str
    ) -> ChairDocument | None:
        return await self._session.scalar(
            select(ChairDocument).where(
                ChairDocument.chair_id == chair_id,
                ChairDocument.arxiv_id == arxiv_id,
            )
        )

    async def add_document(
        self,
        *,
        chair_id: int,
        kind: ChairDocumentKind,
        content: str,
        title: str | None = None,
        arxiv_id: str | None = None,
        published_year: int | None = None,
        embedding: list[float] | None = None,
    ) -> ChairDocument:
        doc = ChairDocument(
            chair_id=chair_id,
            kind=kind,
            content=content,
            title=title,
            arxiv_id=arxiv_id,
            published_year=published_year,
            embedding=embedding,
        )
        self._session.add(doc)
        await self._session.flush()
        await self._session.refresh(doc)
        return doc

    async def delete_document(self, doc: ChairDocument) -> None:
        await self._session.delete(doc)
        await self._session.flush()

    async def search_by_embedding(
        self, embedding: list[float], k: int = 5
    ) -> list[dict]:
        """ANN search over chair_documents; returns top-k with chair metadata."""
        stmt = (
            select(
                ChairDocument,
                ChairDocument.embedding.cosine_distance(embedding).label("distance"),
            )
            .where(ChairDocument.embedding.is_not(None))
            .order_by("distance")
            .limit(k)
            .options(selectinload(ChairDocument.chair))
        )
        rows = await self._session.execute(stmt)
        results = []
        seen_chairs: set[int] = set()
        for doc, distance in rows:
            chair = doc.chair
            results.append(
                {
                    "chair_id": chair.id,
                    "chair_name": chair.name,
                    "professor_name": chair.professor_name,
                    "short_description": chair.short_description,
                    "document_kind": doc.kind.value,
                    "document_title": doc.title,
                    "snippet": doc.content[:300],
                    "score": round(1 - distance, 4),
                    "already_seen": chair.id in seen_chairs,
                }
            )
            seen_chairs.add(chair.id)
        return results

    async def commit(self) -> None:
        await self._session.commit()
