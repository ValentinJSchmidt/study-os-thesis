"""Smoke-test the search tool against whatever is in the DB.

Run from backend/:
    uv run python scripts/check_search.py "deep learning on graphs"
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.db import SessionLocal
from app.llm.ollama_client import OllamaClient
from app.tools.search_theses import search_theses_with_client


async def main(query: str) -> None:
    settings = get_settings()
    client = OllamaClient(host=settings.ollama_host)
    async with SessionLocal() as session:
        hits = await search_theses_with_client(client, settings, query, k=5, session=session)
    for h in hits:
        print(f"[{h['score']:.3f}] {h['id']}: {h['title']}")
        print(f"    {h['abstract'][:120]}...")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "machine learning"
    asyncio.run(main(q))
