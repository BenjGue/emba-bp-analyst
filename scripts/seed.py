"""Jeu de données de démonstration BizPlan-IA (BIZ-23).

Insère des projets fictifs représentatifs des directions de La Poste, avec
hypothèses financières, évaluation stratégique (donc score) et business plan
généré. Idempotent : un projet déjà présent (même nom) n'est pas recréé.

Usage :
    python -m scripts.seed
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine, init_db
from app.models import Project
from app.schemas.financial import FinancialAssumptionCreate
from app.schemas.project import Direction, ProjectCreate
from app.schemas.score import StrategicDimensions
from app.services.financials import save_financials
from app.services.generation import generate_business_plan
from app.services.projects import create_project, save_dimensions

#: Projets de démonstration : (projet, hypothèses financières, dimensions).
_DEMO: list[tuple[ProjectCreate, FinancialAssumptionCreate, StrategicDimensions]] = [
    (
        ProjectCreate(
            nom="Casiers connectés en bureau de poste",
            description=(
                "Déployer des casiers automatiques connectés pour le retrait "
                "de colis en libre-service dans les bureaux de poste."
            ),
            direction=Direction.SERVICES_COURRIER_COLIS,
            duree_estimee_mois=18,
        ),
        FinancialAssumptionCreate(
            investissement_initial=450000,
            revenus_annuels=320000,
            couts_annuels=120000,
            delai_rentabilite_mois=30,
        ),
        StrategicDimensions(
            rentabilite=8,
            alignement=9,
            risque=7,
            impact_operationnel=8,
            impact_social=6,
            faisabilite=8,
        ),
    ),
    (
        ProjectCreate(
            nom="Assistant budgétaire IA pour La Banque Postale",
            description=(
                "Proposer un assistant intelligent d'aide à la gestion de "
                "budget personnel dans l'application bancaire."
            ),
            direction=Direction.LA_BANQUE_POSTALE,
            duree_estimee_mois=12,
        ),
        FinancialAssumptionCreate(
            investissement_initial=600000,
            revenus_annuels=500000,
            couts_annuels=180000,
            delai_rentabilite_mois=24,
        ),
        StrategicDimensions(
            rentabilite=9,
            alignement=8,
            risque=6,
            impact_operationnel=7,
            impact_social=8,
            faisabilite=7,
        ),
    ),
    (
        ProjectCreate(
            nom="Tournées de livraison optimisées par IA",
            description=(
                "Optimiser les tournées des facteurs grâce à un moteur "
                "d'optimisation tenant compte du trafic et des contraintes."
            ),
            direction=Direction.GEOPOST,
            duree_estimee_mois=15,
        ),
        FinancialAssumptionCreate(
            investissement_initial=380000,
            revenus_annuels=210000,
            couts_annuels=140000,
            delai_rentabilite_mois=42,
        ),
        StrategicDimensions(
            rentabilite=6,
            alignement=7,
            risque=5,
            impact_operationnel=8,
            impact_social=5,
            faisabilite=6,
        ),
    ),
    (
        ProjectCreate(
            nom="Plateforme de formation interne immersive",
            description=(
                "Créer une plateforme de formation en réalité virtuelle pour "
                "les agents du réseau La Poste."
            ),
            direction=Direction.RESEAU_LA_POSTE,
            duree_estimee_mois=20,
        ),
        FinancialAssumptionCreate(
            investissement_initial=520000,
            revenus_annuels=90000,
            couts_annuels=110000,
            delai_rentabilite_mois=72,
        ),
        StrategicDimensions(
            rentabilite=2,
            alignement=5,
            risque=4,
            impact_operationnel=4,
            impact_social=6,
            faisabilite=3,
        ),
    ),
    (
        ProjectCreate(
            nom="Portail RSE de suivi carbone des sites",
            description=(
                "Mettre en place un portail de mesure et de pilotage de "
                "l'empreinte carbone des sites du groupe."
            ),
            direction=Direction.LA_POSTE_GROUPE,
            duree_estimee_mois=14,
        ),
        FinancialAssumptionCreate(
            investissement_initial=300000,
            revenus_annuels=150000,
            couts_annuels=80000,
            delai_rentabilite_mois=48,
        ),
        StrategicDimensions(
            rentabilite=5,
            alignement=8,
            risque=6,
            impact_operationnel=5,
            impact_social=9,
            faisabilite=7,
        ),
    ),
    (
        ProjectCreate(
            nom="Signature électronique pour les services numériques",
            description=(
                "Industrialiser une brique de signature électronique "
                "réutilisable par les services numériques du groupe."
            ),
            direction=Direction.NUMERIQUE,
            duree_estimee_mois=10,
        ),
        FinancialAssumptionCreate(
            investissement_initial=250000,
            revenus_annuels=280000,
            couts_annuels=90000,
            delai_rentabilite_mois=18,
        ),
        StrategicDimensions(
            rentabilite=9,
            alignement=8,
            risque=8,
            impact_operationnel=7,
            impact_social=6,
            faisabilite=9,
        ),
    ),
]


def seed() -> int:
    """Insère les projets de démonstration manquants.

    Returns:
        Le nombre de projets créés lors de cet appel.
    """
    init_db()
    created = 0
    with Session(get_engine()) as session:
        for project_data, financials_data, dimensions in _DEMO:
            exists = session.execute(
                select(Project).where(Project.nom == project_data.nom)
            ).scalar_one_or_none()
            if exists is not None:
                continue
            project = create_project(session, project_data)
            save_financials(session, project.id, financials_data)
            save_dimensions(session, project.id, dimensions)
            generate_business_plan(session, project.id)
            created += 1
    return created


if __name__ == "__main__":
    count = seed()
    print(f"{count} projet(s) de démonstration créé(s).")
