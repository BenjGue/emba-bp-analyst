"""Rédaction assistée par IA de la description d'un projet (BIZ-37).

À partir de quelques idées clés saisies par le porteur, l'IA rédige une
description complète et structurée. Le backend borne ensuite la longueur du
texte produit pour respecter la contrainte de ``ProjectCreate.description``
(1000 caractères), illustrant le principe « l'IA propose, le backend valide ».
"""

from __future__ import annotations

from app.schemas.ai import DescriptionDraftRequest, DescriptionDraftResponse
from app.services.ai.client import AiClient
from app.services.ai.prompts import DESCRIPTION_SYSTEM

#: Longueur maximale de la description (alignée sur ``ProjectCreate``).
_MAX_DESCRIPTION_LEN = 1000


def _build_user_prompt(request: DescriptionDraftRequest) -> str:
    """Compose le message utilisateur transmis au modèle.

    Args:
        request: Idées clés et contexte fournis par le porteur.

    Returns:
        Le prompt utilisateur prêt à être envoyé.
    """
    lignes = [f"Direction concernée : {request.direction.value}"]
    if request.nom:
        lignes.append(f"Nom du projet : {request.nom}")
    lignes.append(f"Idées clés à développer :\n{request.idees}")
    return "\n".join(lignes)


def draft_description(
    request: DescriptionDraftRequest,
    *,
    client: AiClient,
) -> DescriptionDraftResponse:
    """Génère une description de projet à partir d'idées clés.

    Args:
        request: Idées clés et contexte fournis par le porteur.
        client: Client IA injecté (facilite les tests hors-ligne).

    Returns:
        La description rédigée, bornée à 1000 caractères.

    Raises:
        AiResponseError: Si le modèle ne renvoie aucun contenu exploitable.
    """
    completion = client.complete(
        system=DESCRIPTION_SYSTEM,
        user=_build_user_prompt(request),
        json_mode=False,
    )
    description = completion.text.strip()[:_MAX_DESCRIPTION_LEN].strip()
    return DescriptionDraftResponse(description=description)
