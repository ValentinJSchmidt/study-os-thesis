"""Hybrid thesis search: vector similarity + BM25 keyword ranking fused with RRF.

Strategy
--------
1. **Vector leg** — embed the query via Ollama and run a cosine-distance ANN
   search using the HNSW index on `theses.embedding`.  Returns up to `k*3`
   candidates ranked by semantic similarity.

2. **BM25 leg** — run a PostgreSQL full-text search on the `search_vec`
   generated tsvector column (backed by a GIN index) using `ts_rank_cd`.
   Returns up to `k*3` candidates ranked by keyword relevance.

3. **Reciprocal Rank Fusion (RRF)** — combine the two ranked lists in Python:
       rrf_score(d) = Σ  1 / (rank_in_list + RRF_K)
   where RRF_K = 60 (the standard constant from Cormack et al. 2009).
   Theses appearing in both lists get a higher combined score.  The final
   list is sorted by combined score descending and trimmed to `k` results.

Fallback behaviour
------------------
* Ollama offline  → vector leg is skipped; BM25-only results are returned.
* No BM25 hits    → vector-only results are returned.
* Both legs empty → empty list returned.
"""

import asyncio
import logging
from typing import TypedDict

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.llm.port import LLMPort

_logger = logging.getLogger(__name__)

# Standard RRF constant (Cormack, Clarke & Buettcher, SIGIR 2009).
RRF_K = 60


class ThesisHit(TypedDict):
    id: int
    title: str
    abstract: str
    score: float


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _rrf_fuse(
    vector_rows: list[tuple],  # (id, title, abstract, distance)
    bm25_rows: list[tuple],  # (id, title, abstract, rank)
) -> list[ThesisHit]:
    """Merge two ranked lists with Reciprocal Rank Fusion."""
    # Accumulate RRF scores and store metadata keyed by thesis id.
    scores: dict[int, float] = {}
    meta: dict[int, tuple[str, str]] = {}  # id -> (title, abstract)

    for rank, row in enumerate(vector_rows):
        tid, title, abstract = row[0], row[1], row[2]
        scores[tid] = scores.get(tid, 0.0) + 1.0 / (rank + 1 + RRF_K)
        meta[tid] = (title, abstract)

    for rank, row in enumerate(bm25_rows):
        tid, title, abstract = row[0], row[1], row[2]
        scores[tid] = scores.get(tid, 0.0) + 1.0 / (rank + 1 + RRF_K)
        meta[tid] = (title, abstract)

    sorted_ids = sorted(scores, key=lambda i: scores[i], reverse=True)
    return [
        ThesisHit(
            id=tid,
            title=meta[tid][0],
            abstract=meta[tid][1],
            score=round(scores[tid], 6),
        )
        for tid in sorted_ids
    ]


async def _vector_search(
    session: AsyncSession,
    ollama: LLMPort,
    settings: Settings,
    query: str,
    fetch: int,
    chair_id: int | None = None,
) -> list[tuple]:
    """Return up to `fetch` rows ordered by cosine distance (ascending).

    Returns an empty list if Ollama is unreachable.
    """
    try:
        q_vec = await ollama.embed(settings.ollama_embed_model, query)
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        _logger.warning("Vector search skipped — Ollama unavailable: %s", exc)
        return []

    chair_filter = "AND chair_id = :chair_id" if chair_id is not None else ""
    stmt = text(
        f"""
        SELECT id, title, abstract,
               embedding <=> CAST(:vec AS vector) AS distance
        FROM   theses
        WHERE  embedding IS NOT NULL
        {chair_filter}
        ORDER  BY distance ASC
        LIMIT  :lim
        """
    ).bindparams(vec=str(q_vec), lim=fetch, **({"chair_id": chair_id} if chair_id is not None else {}))

    rows = (await session.execute(stmt)).all()
    return list(rows)


async def _bm25_search(
    session: AsyncSession,
    query: str,
    fetch: int,
    chair_id: int | None = None,
) -> list[tuple]:
    """Return up to `fetch` rows ordered by ts_rank_cd (descending)."""
    chair_filter = "AND chair_id = :chair_id" if chair_id is not None else ""
    stmt = text(
        f"""
        SELECT id, title, abstract,
               ts_rank_cd(search_vec, plainto_tsquery('english', :q)) AS rank
        FROM   theses
        WHERE  search_vec @@ plainto_tsquery('english', :q)
        {chair_filter}
        ORDER  BY rank DESC
        LIMIT  :lim
        """
    ).bindparams(q=query, lim=fetch, **({"chair_id": chair_id} if chair_id is not None else {}))

    rows = (await session.execute(stmt)).all()
    return list(rows)


# ---------------------------------------------------------------------------
# Public API (signature unchanged — all callers continue to work as-is)
# ---------------------------------------------------------------------------


async def search_theses_with_client(
    ollama: LLMPort,
    settings: Settings,
    query: str,
    k: int = 5,
    *,
    session: AsyncSession | None = None,
    chair_id: int | None = None,
) -> list[ThesisHit]:
    """Hybrid semantic + keyword search over the thesis database.

    Uses the injected *ollama* client and *settings* for vector search, and
    PostgreSQL full-text search for BM25.  Results are fused with RRF.

    If *session* is None a new session is created from ``SessionLocal``.
    Optionally filter results to a specific chair via *chair_id*.
    """
    from app.db import SessionLocal  # deferred to avoid circular import

    k = max(1, min(k, 20))
    fetch = k * 3  # over-fetch so RRF has enough candidates from each leg

    async def _run(s: AsyncSession) -> list[ThesisHit]:
        vector_task = _vector_search(s, ollama, settings, query, fetch, chair_id=chair_id)
        bm25_task = _bm25_search(s, query, fetch, chair_id=chair_id)
        vector_rows, bm25_rows = await asyncio.gather(vector_task, bm25_task)

        if not vector_rows and not bm25_rows:
            return []

        fused = _rrf_fuse(vector_rows, bm25_rows)
        return fused[:k]

    if session is not None:
        return await _run(session)
    else:
        async with SessionLocal() as s:
            return await _run(s)
