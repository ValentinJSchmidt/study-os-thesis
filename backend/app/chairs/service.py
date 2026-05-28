"""Business logic for research chairs and ArXiv paper ingestion."""

import logging
import xml.etree.ElementTree as ET

import httpx

from app.chairs.repository import ChairRepository
from app.chairs.schemas import ArxivIngestRequest, ChairCreate, ChairPatch
from app.config import Settings
from app.exceptions import AlreadyExistsException, BadRequestException, NotFoundException
from app.llm.port import LLMPort
from app.models.chair import Chair, ChairDocument, ChairDocumentKind

_logger = logging.getLogger(__name__)

_ARXIV_API = "https://export.arxiv.org/api/query"
_ARXIV_NS = "http://www.w3.org/2005/Atom"


class ChairService:
    def __init__(
        self,
        chair_repo: ChairRepository,
        embed_client: LLMPort,
        settings: Settings,
    ) -> None:
        self._chair_repo = chair_repo
        self._ollama = embed_client
        self._settings = settings

    # ------------------------------------------------------------------
    # Chair CRUD
    # ------------------------------------------------------------------

    async def create_chair(self, data: ChairCreate, *, embed: bool = True) -> Chair:
        _logger.info("Creating chair: name=%r professor=%r", data.name, data.professor_name)
        chair = await self._chair_repo.create(
            name=data.name,
            short_description=data.short_description,
            professor_name=data.professor_name,
            professor_user_id=data.professor_user_id,
            website_url=data.website_url,
        )
        if embed:
            _logger.info("Chair created: id=%d — embedding description document", chair.id)
            embedding = await self._embed_text(data.short_description)
            await self._chair_repo.add_document(
                chair_id=chair.id,
                kind=ChairDocumentKind.description,
                content=data.short_description,
                embedding=embedding,
            )
        await self._chair_repo.commit()
        _logger.info("Chair id=%d committed to DB", chair.id)
        return await self._chair_repo.get_by_id(chair.id, load_documents=True)  # type: ignore[return-value]

    async def get_chair(self, chair_id: int) -> Chair:
        chair = await self._chair_repo.get_by_id(chair_id, load_documents=True)
        if chair is None:
            raise NotFoundException("Chair", chair_id)
        return chair

    async def list_chairs(self) -> list[Chair]:
        return await self._chair_repo.list()

    async def update_chair(self, chair_id: int, data: ChairPatch) -> Chair:
        chair = await self._chair_repo.get_by_id(chair_id)
        if chair is None:
            raise NotFoundException("Chair", chair_id)
        updates = data.model_dump(exclude_none=True)
        chair = await self._chair_repo.update(chair, **updates)
        await self._chair_repo.commit()
        return await self._chair_repo.get_by_id(chair_id, load_documents=True)  # type: ignore[return-value]

    async def delete_chair(self, chair_id: int) -> None:
        chair = await self._chair_repo.get_by_id(chair_id)
        if chair is None:
            raise NotFoundException("Chair", chair_id)
        await self._chair_repo.delete(chair)
        await self._chair_repo.commit()

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------

    async def ingest_arxiv_paper(self, chair_id: int, req: ArxivIngestRequest) -> ChairDocument:
        _logger.info("ArXiv ingest started: chair_id=%d arxiv_id=%r", chair_id, req.arxiv_id)
        chair = await self._chair_repo.get_by_id(chair_id)
        if chair is None:
            raise NotFoundException("Chair", chair_id)

        existing = await self._chair_repo.get_document_by_arxiv(chair_id, req.arxiv_id)
        if existing is not None:
            raise AlreadyExistsException("ChairDocument", "arxiv_id", req.arxiv_id)

        _logger.info("Fetching metadata from ArXiv for id=%r", req.arxiv_id)
        title, abstract, year = await _fetch_arxiv_metadata(req.arxiv_id)
        _logger.info("ArXiv metadata fetched: title=%r year=%s abstract_len=%d", title, year, len(abstract))

        _logger.info("Creating embedding for ArXiv paper %r (model=%s)", req.arxiv_id, self._settings.ollama_embed_model)
        embedding = await self._embed_text(abstract)
        if embedding is not None:
            _logger.info("Embedding created for ArXiv paper %r: dim=%d", req.arxiv_id, len(embedding))
        else:
            _logger.warning("Embedding failed for ArXiv paper %r — stored without embedding", req.arxiv_id)

        doc = await self._chair_repo.add_document(
            chair_id=chair_id,
            kind=ChairDocumentKind.paper,
            content=abstract,
            title=title,
            arxiv_id=req.arxiv_id,
            published_year=year,
            embedding=embedding,
        )
        await self._chair_repo.commit()
        _logger.info("ArXiv paper %r inserted as document id=%d for chair_id=%d", req.arxiv_id, doc.id, chair_id)
        return doc

    async def delete_document(self, chair_id: int, doc_id: int) -> None:
        doc = await self._chair_repo.get_document(doc_id)
        if doc is None or doc.chair_id != chair_id:
            raise NotFoundException("ChairDocument", doc_id)
        await self._chair_repo.delete_document(doc)
        await self._chair_repo.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _embed_text(self, text: str) -> list[float] | None:
        _logger.info("Embedding text: model=%s text_len=%d", self._settings.ollama_embed_model, len(text))
        try:
            vec = await self._ollama.embed(self._settings.ollama_embed_model, text)
            _logger.info("Embedding done: dim=%d", len(vec))
            return vec
        except Exception as exc:
            _logger.warning("Embedding failed, document stored without embedding: %s", exc)
            return None


async def _fetch_arxiv_metadata(arxiv_id: str) -> tuple[str, str, int | None]:
    """Fetch title, abstract, and publication year from the ArXiv Atom API."""
    url = f"{_ARXIV_API}?id_list={arxiv_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise BadRequestException(f"ArXiv API returned {exc.response.status_code} for id '{arxiv_id}'") from exc
        except httpx.RequestError as exc:
            raise BadRequestException(f"Could not reach ArXiv API: {exc}") from exc

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        raise BadRequestException("ArXiv API returned invalid XML.") from exc

    entry = root.find(f"{{{_ARXIV_NS}}}entry")
    if entry is None:
        raise NotFoundException("ArXiv paper", arxiv_id)  # type: ignore[arg-type]

    title_el = entry.find(f"{{{_ARXIV_NS}}}title")
    summary_el = entry.find(f"{{{_ARXIV_NS}}}summary")
    published_el = entry.find(f"{{{_ARXIV_NS}}}published")

    title = (title_el.text or "").strip() if title_el is not None else ""
    abstract = (summary_el.text or "").strip() if summary_el is not None else ""
    year: int | None = None
    if published_el is not None and published_el.text:
        try:
            year = int(published_el.text[:4])
        except ValueError:
            pass

    if not abstract:
        raise BadRequestException(f"ArXiv paper '{arxiv_id}' has no abstract or was not found.")

    return title, abstract, year
