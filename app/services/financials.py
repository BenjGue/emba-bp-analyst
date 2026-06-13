"""Service de gestion des hypothèses financières (US-1.2).

Création ou mise à jour (une seule occurrence par projet) et lecture des
hypothèses financières rattachées à un projet existant.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import FinancialAssumption
from app.schemas.financial import FinancialAssumptionCreate
from app.services.projects import get_project


class FinancialsNotFoundError(Exception):
    """Levée lorsqu'aucune hypothèse financière n'existe pour le projet."""


def save_financials(
    db: Session,
    project_id: int,
    data: FinancialAssumptionCreate,
) -> FinancialAssumption:
    """Crée ou met à jour les hypothèses financières d'un projet.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet rattaché.
        data: Hypothèses financières validées.

    Returns:
        Les hypothèses financières persistées.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
    """
    project = get_project(db, project_id)

    assumption = project.financial_assumption
    if assumption is None:
        assumption = FinancialAssumption(project_id=project_id)
        db.add(assumption)
    assumption.investissement_initial = data.investissement_initial
    assumption.revenus_annuels = data.revenus_annuels
    assumption.couts_annuels = data.couts_annuels
    assumption.delai_rentabilite_mois = data.delai_rentabilite_mois

    db.commit()
    db.refresh(assumption)
    return assumption


def get_financials(db: Session, project_id: int) -> FinancialAssumption:
    """Retourne les hypothèses financières d'un projet.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet rattaché.

    Returns:
        Les hypothèses financières persistées.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
        FinancialsNotFoundError: Si aucune hypothèse n'a été saisie.
    """
    project = get_project(db, project_id)
    if project.financial_assumption is None:
        raise FinancialsNotFoundError(project_id)
    return project.financial_assumption
