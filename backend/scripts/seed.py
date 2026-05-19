"""Idempotent database seed script.

Inserts the 3 Tübingen CS chairs with their description documents and
embeddings. If any chairs already exist in the DB, the script does nothing.

Run from the backend directory:
    uv run python scripts/seed.py
"""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
_logger = logging.getLogger("seed")

CHAIRS = [
    {
        "name": "Lehrstuhl für Theorie des Maschinellen Lernens (TML)",
        "professor_name": "Prof. Dr. Ulrike von Luxburg",
        "website_url": "https://www.tml.cs.uni-tuebingen.de",
        "short_description": (
            "Die Forschungsgruppe Theory of Machine Learning (TML) untersucht maschinelle "
            "Lernverfahren aus theoretischer Perspektive. Schwerpunkte sind erklärbare KI "
            "(Explainability), formale statistische Garantien für die Performance von ML-Algorithmen, "
            "implizite Annahmen und versteckte Biases in verbreiteten Verfahren sowie Bedingungen, "
            "unter denen Algorithmen wie Random Forests oder Spektralclustering nachweislich versagen. "
            "Weitere Themen umfassen Vergleichsbasiertes Clustering, ordinales Embedding und "
            "Konsistenz von Spektralmethoden. Die Gruppe legt großen Wert auf mathematisch rigorose "
            "Beweise und die formale Analyse von LIME, SHAP und anderen Post-hoc-Erklärungsverfahren."
        ),
    },
    {
        "name": "Lehrstuhl für Autonomes Maschinelles Sehen",
        "professor_name": "Prof. Dr. Andreas Geiger",
        "website_url": (
            "https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/"
            "fachbereiche/informatik/lehrstuehle/autonomous-vision/home/"
        ),
        "short_description": (
            "Die Forschungsgruppe Autonomous Vision beschäftigt sich mit 3D-Szenenverständnis, "
            "Rekonstruktion, Bewegungsschätzung, generativer Modellierung und sensomotorischer "
            "Steuerung für autonome Systeme wie selbstfahrende Fahrzeuge und Haushaltsroboter. "
            "Kernthemen sind kompakte 3D-Repräsentationen aus 2D/3D-Messungen, Integration von "
            "Vorwissen in Wahrnehmungsmodelle, Lernen mit wenig annotierten Daten (Self-Supervised "
            "Learning), generative Modelle (GANs, VAEs) für Datengenerierung im autonomen Fahren, "
            "end-to-end trainierbare Modelle sowie die Erstellung von Benchmark-Datensätzen wie "
            "KITTI und KITTI-360. Zusätzlich wird Forschung zur Integration von Sprache und Vision "
            "sowie zur Beschleunigung des wissenschaftlichen Prozesses (Scholar Inbox) betrieben."
        ),
    },
    {
        "name": "Lehrstuhl für Distributed Intelligence",
        "professor_name": "Prof. Dr. Georg Martius",
        "website_url": (
            "https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/"
            "fachbereiche/informatik/lehrstuehle/distributed-intelligence/home/"
        ),
        "short_description": (
            "Die Forschungsgruppe Distributed Intelligence forscht an modellbasiertem und "
            "modellfreiem Reinforcement Learning, Deep Learning, kombinatorischer Optimierung, "
            "haptischer Sensorik und ML für Wissenschaft. Konkrete Themen umfassen: iCEM für "
            "modellbasierte Planung, Policy Extraction, risikoaverses Planen, kausales Schlussfolgern "
            "in RL, intrinsisch motiviertes hierarchisches Lernen, Representation Learning, "
            "probabilistische neuronale Netze, Deep Graph Matching, CombOptNet, haptische Sensoren "
            "mit Vision und ML (Insight), Vorhersage von Hirnaktivität (fMRI), symbolische Regression "
            "und Gleichungslernen sowie ML für Quantensysteme und statistische Physik."
        ),
    },
]


async def main() -> None:
    from sqlalchemy import func, select

    from app.config import get_settings
    from app.db import SessionLocal
    from app.llm.ollama_client import OllamaClient
    from app.models.chair import Chair, ChairDocument, ChairDocumentKind

    settings = get_settings()

    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Chair))
        if count and count > 0:
            _logger.info("Database already contains %d chair(s) — skipping seed.", count)
            return

    _logger.info("Seeding %d chairs...", len(CHAIRS))

    async with OllamaClient() as ollama:
        async with SessionLocal() as session:
            for data in CHAIRS:
                chair = Chair(
                    name=data["name"],
                    short_description=data["short_description"],
                    professor_name=data["professor_name"],
                    website_url=data["website_url"],
                )
                session.add(chair)
                await session.flush()
                await session.refresh(chair)
                _logger.info("  Created chair id=%d: %s", chair.id, chair.name)

                # Embed the description.
                embedding = None
                try:
                    embedding = await ollama.embed(
                        settings.ollama_embed_model, data["short_description"]
                    )
                    _logger.info("    Embedding created: dim=%d", len(embedding))
                except Exception as exc:
                    _logger.warning("    Embedding failed (Ollama offline?): %s", exc)

                doc = ChairDocument(
                    chair_id=chair.id,
                    kind=ChairDocumentKind.description,
                    content=data["short_description"],
                    embedding=embedding,
                )
                session.add(doc)

            await session.commit()

    _logger.info("Seed complete: %d chairs inserted.", len(CHAIRS))


if __name__ == "__main__":
    asyncio.run(main())
