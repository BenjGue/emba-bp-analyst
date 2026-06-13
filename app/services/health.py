"""Service du healthcheck.

Contient la logique métier (minimale) du healthcheck, séparée du router afin de
respecter la règle « pas de logique métier dans les routers ».
"""

from __future__ import annotations

from app import __version__
from app.config import Settings
from app.schemas.health import HealthResponse


def get_health(settings: Settings) -> HealthResponse:
    """Construit la réponse de healthcheck à partir de la configuration.

    Args:
        settings: Configuration applicative courante.

    Returns:
        La réponse de healthcheck indiquant que l'application est opérationnelle.
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=__version__,
    )
