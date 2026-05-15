"""Smoke-test: verify Ollama is up and the embedding model returns 768d vectors.

Run from backend/:
    uv run python scripts/check_ollama.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm.embeddings import embed_text  # noqa: E402


async def main() -> None:
    vec = await embed_text("hello world")
    print(f"dim = {len(vec)}")
    print(f"first 5 = {vec[:5]}")
    assert len(vec) == 768, f"expected 768d, got {len(vec)}"
    print("ok")


if __name__ == "__main__":
    asyncio.run(main())
