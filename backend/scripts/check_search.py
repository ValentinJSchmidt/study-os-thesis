"""Smoke-test the search tool against whatever is in the DB.

Run from backend/:
    uv run python scripts/check_search.py "deep learning on graphs"
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal  # noqa: E402
from app.tools.search_theses import search_theses  # noqa: E402


async def main(query: str) -> None:
    async with SessionLocal() as session:
        hits = await search_theses(session, query, k=5)
    for h in hits:
        print(f"[{h['score']:.3f}] {h['id']}: {h['title']}")
        print(f"    {h['abstract'][:120]}...")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "machine learning"
    asyncio.run(main(q))
