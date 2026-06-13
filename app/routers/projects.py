"""Router de scoring rattaché à un projet (US-2.2).

Expose ``POST /projects/{project_id}/score`` qui calcule et persiste le score
de pertinence d'un projet existant.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.score import ScoreResponse, StrategicDimensions
from app.services.projects import ProjectNotFoundError, score_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/{project_id}/score",
    response_model=ScoreResponse,
    summary="Calculer et persister le score d'un projet",
)
def create_project_score(
    project_id: int,
    dimensions: StrategicDimensions,
    db: Annotated[Session, Depends(get_db)],
) -> ScoreResponse:
    """Calcule et persiste le score de pertinence d'un projet.

    Args:
        project_id: Identifiant du projet à évaluer.
        dimensions: Notes stratégiques (6 dimensions, entiers 0-10).
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le score global (0-100) et le détail par dimension.

    Raises:
        HTTPException: 404 si le projet n'existe pas.
    """
    try:
        return score_project(db, project_id, dimensions)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet introuvable",
        ) from exc
