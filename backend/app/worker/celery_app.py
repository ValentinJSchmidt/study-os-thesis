"""Celery application instance for study-os-thesis."""

from celery import Celery
from celery.signals import worker_process_init

celery_app = Celery("study_os_thesis")
celery_app.config_from_object("app.worker.celery_config")
celery_app.autodiscover_tasks(
    [
        "app.theses",
        "app.chairs",
        "app.students",
        "app.chat",
    ]
)


@worker_process_init.connect
def _init_worker_engine(**_kwargs: object) -> None:
    """Re-create the async DB engine after the prefork worker forks.

    The engine/connection pool inherited across ``fork()`` is bound to the
    parent's event loop and is unsafe to use in the child. We dispose it and
    rebuild with ``NullPool`` so every task opens (and closes) its own
    connection on the fresh event loop that ``run_async`` creates per call.
    """
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    import app.db as db

    asyncio.run(db.engine.dispose())

    db.engine = create_async_engine(db.settings.database_url, echo=False, future=True, poolclass=NullPool)
    db.SessionLocal = async_sessionmaker(db.engine, expire_on_commit=False, class_=db.AsyncSession)
