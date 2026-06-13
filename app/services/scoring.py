"""Service de calcul du score de pertinence (US-2.1).

Calcul **déterministe** et auditable du score de pertinence sur 6 dimensions
pondérées. Aucune dépendance externe ni appel IA : mêmes entrées → même sortie.
"""

from __future__ import annotations

from typing import Final

from app.schemas.score import DimensionDetail, ScoreResponse, StrategicDimensions

#: Pondération de chaque dimension. La somme vaut exactement ``1.0``.
WEIGHTS: Final[dict[str, float]] = {
    "rentabilite": 0.30,
    "alignement": 0.20,
    "risque": 0.20,
    "impact_operationnel": 0.10,
    "impact_social": 0.10,
    "faisabilite": 0.10,
}

#: Note maximale possible sur chaque dimension (échelle 0-10).
_MAX_NOTE: Final[int] = 10

#: Score maximal global (échelle 0-100).
_MAX_SCORE: Final[int] = 100


def compute_score(dimensions: StrategicDimensions) -> ScoreResponse:
    """Calcule le score de pertinence à partir des dimensions stratégiques.

    Formule : pour chaque dimension, la note ``[0, 10]`` est normalisée dans
    ``[0, 1]`` puis multipliée par sa pondération et par 100. La somme des
    contributions donne le score global, borné strictement dans ``[0, 100]``.

    Args:
        dimensions: Notes stratégiques saisies (entiers 0-10).

    Returns:
        Le score global et le détail de la contribution de chaque dimension.
    """
    details: dict[str, DimensionDetail] = {}
    total = 0.0

    for name, weight in WEIGHTS.items():
        note: int = getattr(dimensions, name)
        contribution = (note / _MAX_NOTE) * weight * _MAX_SCORE
        total += contribution
        details[name] = DimensionDetail(
            note=note,
            poids=weight,
            contribution=round(contribution, 2),
        )

    bounded_total = max(0.0, min(float(_MAX_SCORE), round(total, 2)))
    return ScoreResponse(total=bounded_total, dimensions=details)
