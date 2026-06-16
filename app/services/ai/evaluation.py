"""Proposition assistée par IA des notes stratégiques (BIZ-56).

À partir des données saisies en partie A (description, direction, durée et,
si disponibles, hypothèses financières), l'IA propose les 6 notes stratégiques,
les justifie et fournit une synthèse de sa logique. Le backend borne les notes
dans ``[0, 10]`` puis calcule le score de façon déterministe : « l'IA propose,
le backend valide et calcule ».
"""

from __future__ import annotations

from typing import Final

from app.schemas.ai import EvaluateurOutput
from app.schemas.score import DimensionSuggestion, StrategicDimensions
from app.services.ai.agents import run_evaluateur
from app.services.ai.client import AiClient
from app.services.scoring import compute_score

#: Bornes admissibles d'une note (échelle 0-10).
_MIN_NOTE: Final[int] = 0
_MAX_NOTE: Final[int] = 10

#: Noms des 6 dimensions stratégiques.
_DIMENSION_NAMES: Final[tuple[str, ...]] = (
    "rentabilite",
    "alignement",
    "risque",
    "impact_operationnel",
    "impact_social",
    "faisabilite",
)


def _clamp(note: int) -> int:
    """Borne une note dans l'intervalle ``[0, 10]``.

    Args:
        note: Note proposée par l'IA (potentiellement hors bornes).

    Returns:
        La note bornée dans ``[0, 10]``.
    """
    return max(_MIN_NOTE, min(_MAX_NOTE, note))


def suggest_dimensions(
    *,
    nom: str,
    description: str,
    direction: str,
    duree_estimee_mois: int,
    financials: dict[str, float] | None,
    client: AiClient,
) -> DimensionSuggestion:
    """Propose les notes stratégiques d'un projet via l'IA (BIZ-56).

    Args:
        nom: Nom du projet.
        description: Description du projet.
        direction: Direction concernée.
        duree_estimee_mois: Horizon temporel estimé, en mois.
        financials: Hypothèses financières clés déjà saisies, ou ``None``.
        client: Client IA injecté (facilite les tests hors-ligne).

    Returns:
        Les notes proposées (bornées), leurs justifications, la synthèse et le
        score déterministe correspondant.

    Raises:
        AiResponseError: Si le modèle ne renvoie aucun contenu exploitable.
    """
    output: EvaluateurOutput = run_evaluateur(
        nom=nom,
        description=description,
        direction=direction,
        duree_estimee_mois=duree_estimee_mois,
        financials=financials,
        client=client,
    )
    dimensions = StrategicDimensions(
        rentabilite=_clamp(output.rentabilite),
        alignement=_clamp(output.alignement),
        risque=_clamp(output.risque),
        impact_operationnel=_clamp(output.impact_operationnel),
        impact_social=_clamp(output.impact_social),
        faisabilite=_clamp(output.faisabilite),
    )
    justifications = {name: output.justifications.get(name, "") for name in _DIMENSION_NAMES}
    return DimensionSuggestion(
        dimensions=dimensions,
        justifications=justifications,
        synthese=output.synthese,
        score=compute_score(dimensions),
    )
