"""Couche d'intégration IA (EPIC 3).

Regroupe le client d'inférence agnostique au modèle, les prompts système des
agents et les erreurs dédiées. La génération multi-agents et la rédaction
assistée s'appuient sur ces briques réutilisables.
"""

from __future__ import annotations

from app.services.ai.client import AiClient, AiCompletion, FoundryClient, get_ai_client
from app.services.ai.errors import (
    AiConfigError,
    AiDisabledError,
    AiError,
    AiResponseError,
)

__all__ = [
    "AiClient",
    "AiCompletion",
    "AiConfigError",
    "AiDisabledError",
    "AiError",
    "AiResponseError",
    "FoundryClient",
    "get_ai_client",
]
