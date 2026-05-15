from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.embeddings import embed_text
from app.models import Thesis


class ThesisHit(TypedDict):
    id: int
    title: str
    abstract: str
    score: float


async def search_theses(session: AsyncSession, query: str, k: int = 5) -> list[ThesisHit]:
    """Embed `query` and return the top-`k` most similar theses by cosine similarity."""
    k = max(1, min(k, 20))
    q_vec = await embed_text(query)

    distance = Thesis.embedding.cosine_distance(q_vec).label("distance")
    stmt = (
        select(Thesis.id, Thesis.title, Thesis.abstract, distance)
        .where(Thesis.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(k)
    )
    rows = (await session.execute(stmt)).all()
    return [
        ThesisHit(
            id=row.id,
            title=row.title,
            abstract=row.abstract,
            score=float(1.0 - row.distance),
        )
        for row in rows
    ]
