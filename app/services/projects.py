"""Services liés aux projets (US-1.1, US-2.2).

Création d'un projet (informations générales) et scoring rattaché à un projet
existant (calcul via ``app.services.scoring`` puis persistance horodatée).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Project, Score
from app.schemas.project import ProjectCreate
from app.schemas.score import ScoreResponse, StrategicDimensions
from app.services.scoring import compute_score


class ProjectNotFoundError(Exception):
    """Levée lorsqu'aucun projet ne correspond à l'identifiant fourni."""


def create_project(db: Session, data: ProjectCreate) -> Project:
    """Crée et persiste un projet à partir de ses informations générales.

    Args:
        db: Session de base de données.
        data: Informations générales validées du projet.

    Returns:
        Le projet persisté, avec son identifiant généré.
    """
    project = Project(
        nom=data.nom,
        description=data.description,
        direction=data.direction.value,
        duree_estimee_mois=data.duree_estimee_mois,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


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
