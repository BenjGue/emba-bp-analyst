"""Router du healthcheck.

Expose ``GET /health`` pour permettre aux sondes (Azure Container Apps, CI) de
vérifier que l'application répond.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.health import HealthResponse
from app.services.health import get_health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Healthcheck")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Vérifie l'état de l'application.

    Args:
        settings: Configuration applicative injectée par FastAPI.

    Returns:
        La réponse de healthcheck avec le statut ``ok``.
    """
    return get_health(settings)
