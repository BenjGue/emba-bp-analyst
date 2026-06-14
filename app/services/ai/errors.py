"""Erreurs spécifiques à la couche d'intégration IA (EPIC 3).

Ces exceptions permettent aux services appelants (rédaction de description,
orchestration multi-agents) de distinguer une IA désactivée d'une réponse
invalide, et d'appliquer le cas échéant un repli déterministe.
"""

from __future__ import annotations


class AiError(Exception):
    """Erreur générique de la couche IA."""


class AiDisabledError(AiError):
    """Levée lorsqu'un appel IA est demandé alors que l'IA est désactivée."""


class AiConfigError(AiError):
    """Levée lorsque la configuration IA est incomplète (endpoint, clé...)."""


class AiResponseError(AiError):
    """Levée lorsque la réponse du modèle est absente, vide ou non exploitable."""
