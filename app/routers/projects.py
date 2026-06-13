"""Routers liés aux projets (EPIC 1, 2, 4).

Expose le cycle de vie d'un projet : création, consultation, mise à jour,
saisie des hypothèses financières et de l'évaluation stratégique, scoring,
génération (mockée), consultation et export du business plan.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.businessplan import BusinessPlanResponse, ScenarioResponse
from app.schemas.financial import (
    FinancialAssumptionCreate,
    FinancialAssumptionResponse,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdate,
)
from app.schemas.score import ScoreResponse, StrategicDimensions
from app.services.export import export_filename, to_markdown, to_pdf
from app.services.financials import (
    FinancialsNotFoundError,
    get_financials,
    save_financials,
)
from app.services.generation import generate_business_plan
from app.services.projects import (
    ProjectNotFoundError,
    create_project,
    delete_project,
    get_project,
    list_project_summaries,
    save_dimensions,
    score_project,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet introuvable")


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un projet",
)
def create_new_project(
    data: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Crée un projet à partir de ses informations générales.

    Args:
        data: Informations générales validées (nom, description, direction,
            durée estimée).
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le projet créé, avec son identifiant et sa date de création.
    """
    project = create_project(db, data)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=list[ProjectSummary],
    summary="Lister les projets (tableau de bord comparatif)",
)
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    direction: Annotated[str | None, Query(description="Filtrer par direction concernée.")] = None,
) -> list[ProjectSummary]:
    """Liste les projets avec leur dernier score, triés par score décroissant.

    Args:
        db: Session de base de données injectée par FastAPI.
        direction: Filtre optionnel sur la direction.

    Returns:
        Les résumés de projets pour le tableau de bord.
    """
    return list_project_summaries(db, direction)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Consulter un projet",
)
def read_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Retourne les informations générales d'un projet.

    Args:
        project_id: Identifiant du projet.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le projet demandé.

    Raises:
        HTTPException: 404 si le projet n'existe pas.
    """
    try:
        return ProjectResponse.model_validate(get_project(db, project_id))
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Modifier un projet",
)
def edit_project(
    project_id: int,
    data: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Met à jour les champs fournis d'un projet (US-1.4).

    Args:
        project_id: Identifiant du projet à modifier.
        data: Champs à mettre à jour.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le projet mis à jour.

    Raises:
        HTTPException: 404 si le projet n'existe pas.
    """
    try:
        return ProjectResponse.model_validate(update_project(db, project_id, data))
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un projet",
)
def remove_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Supprime un projet et ses données rattachées (BIZ-35).

    Args:
        project_id: Identifiant du projet à supprimer.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Une réponse 204 sans contenu.

    Raises:
        HTTPException: 404 si le projet n'existe pas.
    """
    try:
        delete_project(db, project_id)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{project_id}/financials",
    response_model=FinancialAssumptionResponse,
    summary="Saisir les hypothèses financières",
)
def upsert_financials(
    project_id: int,
    data: FinancialAssumptionCreate,
    db: Annotated[Session, Depends(get_db)],
) -> FinancialAssumptionResponse:
    """Crée ou met à jour les hypothèses financières d'un projet (US-1.2).

    Args:
        project_id: Identifiant du projet rattaché.
        data: Hypothèses financières validées.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Les hypothèses financières persistées.

    Raises:
        HTTPException: 404 si le projet n'existe pas.
    """
    try:
        assumption = save_financials(db, project_id, data)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc
    return FinancialAssumptionResponse.model_validate(assumption)


@router.get(
    "/{project_id}/financials",
    response_model=FinancialAssumptionResponse,
    summary="Consulter les hypothèses financières",
)
def read_financials(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> FinancialAssumptionResponse:
    """Retourne les hypothèses financières d'un projet.

    Args:
        project_id: Identifiant du projet rattaché.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Les hypothèses financières persistées.

    Raises:
        HTTPException: 404 si le projet ou les hypothèses n'existent pas.
    """
    try:
        assumption = get_financials(db, project_id)
    except (ProjectNotFoundError, FinancialsNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hypothèses financières introuvables",
        ) from exc
    return FinancialAssumptionResponse.model_validate(assumption)


@router.put(
    "/{project_id}/dimensions",
    response_model=ScoreResponse,
    summary="Saisir les dimensions stratégiques et calculer le score",
)
def upsert_dimensions(
    project_id: int,
    dimensions: StrategicDimensions,
    db: Annotated[Session, Depends(get_db)],
) -> ScoreResponse:
    """Sauvegarde l'évaluation stratégique et calcule le score (US-1.3).

    Args:
        project_id: Identifiant du projet évalué.
        dimensions: Notes stratégiques (6 dimensions, entiers 0-10).
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le score global (0-100) et le détail par dimension.

    Raises:
        HTTPException: 404 si le projet n'existe pas.
    """
    try:
        return save_dimensions(db, project_id, dimensions)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc


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
        raise _NOT_FOUND from exc


@router.get(
    "/{project_id}/score",
    response_model=ScoreResponse,
    summary="Consulter le dernier score d'un projet",
)
def read_score(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ScoreResponse:
    """Retourne le dernier score calculé d'un projet (US-2.3).

    Args:
        project_id: Identifiant du projet.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le dernier score global et le détail par dimension.

    Raises:
        HTTPException: 404 si le projet ou le score n'existe pas.
    """
    try:
        project = get_project(db, project_id)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc
    if not project.scores:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score non calculé")
    last = project.scores[-1]
    return ScoreResponse(total=last.total, dimensions=last.dimensions)


@router.post(
    "/{project_id}/generate",
    response_model=BusinessPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer le business plan (mock)",
)
def generate_bp(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> BusinessPlanResponse:
    """Génère (de façon déterministe) le business plan d'un projet.

    La génération multi-agents IA est différée ; ce mock dérive le contenu des
    données saisies pour débloquer la consultation et l'export.

    Args:
        project_id: Identifiant du projet.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le business plan généré.

    Raises:
        HTTPException: 404 si le projet n'existe pas, 400 si les hypothèses
            financières sont absentes.
    """
    try:
        generate_business_plan(db, project_id)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc
    except FinancialsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hypothèses financières requises avant génération",
        ) from exc
    return _to_bp_response(db, project_id)


@router.get(
    "/{project_id}/bp",
    response_model=BusinessPlanResponse,
    summary="Consulter le business plan généré",
)
def read_bp(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> BusinessPlanResponse:
    """Retourne le business plan généré d'un projet (US-4.1).

    Args:
        project_id: Identifiant du projet.
        db: Session de base de données injectée par FastAPI.

    Returns:
        Le business plan généré.

    Raises:
        HTTPException: 404 si le projet ou le business plan n'existe pas.
    """
    try:
        project = get_project(db, project_id)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc
    if project.business_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business plan non généré"
        )
    return _to_bp_response(db, project_id)


@router.get(
    "/{project_id}/export",
    summary="Exporter le business plan (Markdown ou PDF)",
)
def export_bp(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    export_format: Annotated[str, Query(alias="format", pattern="^(md|pdf)$")] = "md",
) -> Response:
    """Exporte le business plan d'un projet au format Markdown ou PDF (US-4.2).

    Args:
        project_id: Identifiant du projet.
        db: Session de base de données injectée par FastAPI.
        export_format: Format d'export (``md`` ou ``pdf``).

    Returns:
        Le fichier exporté en pièce jointe.

    Raises:
        HTTPException: 404 si le projet ou le business plan n'existe pas.
    """
    try:
        project = get_project(db, project_id)
    except ProjectNotFoundError as exc:
        raise _NOT_FOUND from exc
    if project.business_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business plan non généré"
        )

    if export_format == "pdf":
        content = to_pdf(project, project.business_plan)
        media_type = "application/pdf"
    else:
        content = to_markdown(project, project.business_plan).encode("utf-8")
        media_type = "text/markdown; charset=utf-8"

    filename = export_filename(project, export_format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _to_bp_response(db: Session, project_id: int) -> BusinessPlanResponse:
    """Construit la réponse business plan en agrégeant ses scénarios.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet.

    Returns:
        La représentation API du business plan, scénarios inclus.
    """
    project = get_project(db, project_id)
    bp = project.business_plan
    assert bp is not None  # garanti par les appelants
    scenarios = [
        ScenarioResponse(type=scenario.type, data=scenario.data)
        for scenario in sorted(project.scenarios, key=lambda s: s.type)
    ]
    return BusinessPlanResponse(
        project_id=project_id,
        status=bp.status,
        sections=bp.sections,
        synthese_codir=bp.synthese_codir,
        scenarios=scenarios,
        created_at=bp.created_at,
    )
