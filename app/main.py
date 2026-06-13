"""Point d'entrée de l'application FastAPI.

Assemble l'application, enregistre les routers et expose la documentation
OpenAPI auto-générée sur ``/docs``.
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.routers import health


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
    )
    application.include_router(health.router)
    return application


app = create_app()
