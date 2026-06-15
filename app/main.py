"""Point d'entrée de l'application FastAPI.

Assemble l'application, enregistre les routers et expose la documentation
OpenAPI auto-générée sur ``/docs``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.db import init_db, run_migrations
from app.routers import health, projects, score

_STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialise la base de données au démarrage de l'application.

    Sur SQLite (développement / tests), les tables sont créées directement
    depuis les modèles. Sur une base réelle (MySQL en production), le schéma
    est mis à niveau via les migrations Alembic versionnées (BIZ-29).

    Args:
        application: Instance FastAPI en cours de démarrage.

    Yields:
        Le contrôle pendant la durée de vie de l'application.
    """
    if get_settings().database_url.startswith("sqlite"):
        init_db()
    else:
        run_migrations()
    yield


def create_app() -> FastAPI:
    """Construit et configure l'instance FastAPI.

    Returns:
        L'application FastAPI prête à être servie.
    """
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "API de création automatisée de Business Plans et de scoring de "
            "pertinence de projets internes."
        ),
        lifespan=lifespan,
    )
    application.include_router(health.router)
    application.include_router(score.router)
    application.include_router(projects.router)

    application.mount(
        "/static",
        StaticFiles(directory=_STATIC_DIR),
        name="static",
    )

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Sert l'interface web (single-page application)."""
        return FileResponse(_STATIC_DIR / "index.html")

    return application


app = create_app()
