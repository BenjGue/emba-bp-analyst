"""Dépendances FastAPI de la couche IA (EPIC 3).

Fournit le client IA aux routes via l'injection de dépendances. La fonction est
isolée afin d'être facilement surchargée dans les tests (``dependency_overrides``)
par un faux client, garantissant une CI hors-ligne.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.config import get_settings
from app.services.ai.client import AiClient, get_ai_client
from app.services.ai.errors import AiConfigError


def get_ai_dependency() -> AiClient:
    """Retourne le client IA si la fonctionnalité est activée et configurée.

    Returns:
        Un client IA prêt à l'emploi.

    Raises:
        HTTPException: 503 si l'IA est désactivée ou mal configurée.
    """
    settings = get_settings()
    if not settings.ai_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La rédaction assistée par IA est désactivée sur cet environnement.",
        )
    try:
        return get_ai_client(settings)
    except AiConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La configuration IA est incomplète.",
        ) from exc
