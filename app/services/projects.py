"""Services liés aux projets (US-1.1, US-1.3, US-1.4, US-2.2, US-4.3).

Création, consultation, mise à jour des projets, scoring rattaché et
sauvegarde de l'évaluation stratégique.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project, Score, StrategicAssessment
from app.schemas.project import Direction, ProjectCreate, ProjectSummary, ProjectUpdate
from app.schemas.score import DimensionsSubmission, ScoreResponse, StrategicDimensions
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


def get_project(db: Session, project_id: int) -> Project:
    """Retourne un projet par son identifiant.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet recherché.

    Returns:
        Le projet correspondant.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)
    return project


def update_project(db: Session, project_id: int, data: ProjectUpdate) -> Project:
    """Met à jour les champs fournis d'un projet (US-1.4).

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet à modifier.
        data: Champs à mettre à jour (seuls les champs non nuls sont appliqués).

    Returns:
        Le projet mis à jour.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
    """
    project = get_project(db, project_id)
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in updates.items():
        if field == "direction":
            project.direction = value.value if hasattr(value, "value") else value
        else:
            setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> None:
    """Supprime un projet et ses données rattachées (US-4.3 / BIZ-35).

    La suppression est propagée en cascade aux hypothèses financières, à
    l'évaluation stratégique, aux scores, au business plan et aux scénarios.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet à supprimer.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
    """
    project = get_project(db, project_id)
    db.delete(project)
    db.commit()


def list_project_summaries(db: Session, direction: str | None = None) -> list[ProjectSummary]:
    """Liste les projets avec leur dernier score (US-4.3).

    Args:
        db: Session de base de données.
        direction: Filtre optionnel sur la direction concernée.

    Returns:
        Les résumés de projets, triés par score décroissant (les projets sans
        score apparaissant en dernier).
    """
    stmt = select(Project)
    if direction is not None:
        stmt = stmt.where(Project.direction == direction)
    projects = db.execute(stmt).scalars().all()

    summaries: list[ProjectSummary] = []
    for project in projects:
        last_score = project.scores[-1].total if project.scores else None
        summaries.append(
            ProjectSummary(
                id=project.id,
                nom=project.nom,
                direction=Direction(project.direction),
                score_total=last_score,
                has_business_plan=project.business_plan is not None,
                created_at=project.created_at,
            )
        )

    summaries.sort(
        key=lambda summary: summary.score_total if summary.score_total is not None else -1.0,
        reverse=True,
    )
    return summaries


def save_dimensions(
    db: Session,
    project_id: int,
    dimensions: StrategicDimensions,
) -> ScoreResponse:
    """Sauvegarde l'évaluation stratégique et (re)calcule le score (US-1.3).

    L'évaluation est créée ou mise à jour (une seule par projet), puis le score
    de pertinence est calculé et historisé. Si les notes sont fournies sous
    forme de ``DimensionsSubmission`` (BIZ-56), la synthèse de la logique IA et
    la justification d'une modification manuelle sont conservées pour l'audit.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet évalué.
        dimensions: Notes stratégiques saisies (6 dimensions, 0-10), avec
            éventuellement les champs d'audit ``ai_synthese`` et
            ``justification``.

    Returns:
        Le score global et le détail par dimension.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
    """
    project = get_project(db, project_id)

    assessment = project.strategic_assessment
    if assessment is None:
        assessment = StrategicAssessment(project_id=project_id)
        db.add(assessment)
    assessment.rentabilite = dimensions.rentabilite
    assessment.alignement = dimensions.alignement
    assessment.risque = dimensions.risque
    assessment.impact_operationnel = dimensions.impact_operationnel
    assessment.impact_social = dimensions.impact_social
    assessment.faisabilite = dimensions.faisabilite
    if isinstance(dimensions, DimensionsSubmission):
        assessment.ai_synthese = dimensions.ai_synthese
        assessment.user_justification = dimensions.justification

    result = compute_score(dimensions)
    record = Score(
        project_id=project_id,
        total=result.total,
        dimensions={name: detail.model_dump() for name, detail in result.dimensions.items()},
    )
    db.add(record)
    db.commit()
    return result


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
