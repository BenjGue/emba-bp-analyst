"""Point d'entrée de l'application FastAPI.

Assemble l'application, enregistre les routers et expose la documentation
OpenAPI auto-générée sur ``/docs``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.db import init_db
from app.routers import health, projects, score


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialise la base de données au démarrage de l'application.

    Args:
        application: Instance FastAPI en cours de démarrage.

    Yields:
        Le contrôle pendant la durée de vie de l'application.
    """
    init_db()
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
    return application


app = create_app()
