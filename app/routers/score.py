"""Router du score de pertinence (US-2.1 / US-2.2).

Expose ``POST /score`` qui calcule le score de pertinence d'un projet à partir
des dimensions stratégiques fournies dans le corps de la requête. Le calcul est
pur (pas de persistance ni d'IA), conformément au critère « < 200 ms ».
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.score import ScoreResponse, StrategicDimensions
from app.services.scoring import compute_score

router = APIRouter(tags=["score"])


@router.post("/score", response_model=ScoreResponse, summary="Calculer le score de pertinence")
def score(dimensions: StrategicDimensions) -> ScoreResponse:
    """Calcule le score de pertinence à partir des dimensions stratégiques.

    Args:
        dimensions: Notes stratégiques (6 dimensions, entiers 0-10).

    Returns:
        Le score global (0-100) et le détail par dimension.
    """
    return compute_score(dimensions)
