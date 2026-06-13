"""Service de scoring rattaché à un projet (US-2.2).

Vérifie l'existence du projet, calcule le score (logique pure réutilisée de
``app.services.scoring``) puis persiste le résultat horodaté.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Project, Score
from app.schemas.score import ScoreResponse, StrategicDimensions
from app.services.scoring import compute_score


class ProjectNotFoundError(Exception):
    """Levée lorsqu'aucun projet ne correspond à l'identifiant fourni."""


def score_project(
    db: Session,
    project_id: int,
    dimensions: StrategicDimensions,
) -> ScoreResponse:
    """Calcule et persiste le score de pertinence d'un projet.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet à évaluer.
        dimensions: Notes stratégiques saisies (6 dimensions, 0-10).

    Returns:
        Le score global et le détail par dimension.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
    """
    if db.get(Project, project_id) is None:
        raise ProjectNotFoundError(project_id)

    result = compute_score(dimensions)
    record = Score(
        project_id=project_id,
        total=result.total,
        dimensions={name: detail.model_dump() for name, detail in result.dimensions.items()},
    )
    db.add(record)
    db.commit()
    return result
