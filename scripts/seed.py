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
from app.models import (
    FinancialHypothesis,
    OpportunityType,
    Project,
    RiskType,
    StrategicParameter,
)
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

#: Catalogue de risques types (code, libellé, catégorie, description, sévérité 1-5).
_RISK_TYPES: list[tuple[str, str, str, str, int]] = [
    (
        "tech_obsolescence",
        "Obsolescence technologique",
        "Technique",
        "La solution repose sur une technologie susceptible de devenir obsolète.",
        3,
    ),
    (
        "depassement_budget",
        "Dépassement budgétaire",
        "Financier",
        "Le coût réel du projet excède l'enveloppe initialement prévue.",
        4,
    ),
    (
        "retard_planning",
        "Retard de planning",
        "Projet",
        "Les jalons clés sont livrés après l'échéance planifiée.",
        3,
    ),
    (
        "faible_adoption",
        "Faible adoption utilisateurs",
        "Marché",
        "Les utilisateurs cibles n'adoptent pas le service au rythme attendu.",
        4,
    ),
    (
        "non_conformite_rgpd",
        "Non-conformité RGPD",
        "Réglementaire",
        "Le traitement des données personnelles ne respecte pas la réglementation.",
        5,
    ),
    (
        "dependance_fournisseur",
        "Dépendance à un fournisseur clé",
        "Fournisseur",
        "Le projet dépend fortement d'un prestataire ou éditeur unique.",
        3,
    ),
    (
        "cyberattaque",
        "Incident de cybersécurité",
        "Sécurité",
        "Une compromission de sécurité affecte la disponibilité ou les données.",
        5,
    ),
    (
        "resistance_changement",
        "Résistance au changement interne",
        "Organisationnel",
        "Les équipes internes freinent l'appropriation du nouveau dispositif.",
        3,
    ),
    (
        "indisponibilite_competences",
        "Indisponibilité de compétences",
        "RH",
        "Les compétences nécessaires ne sont pas disponibles au bon moment.",
        4,
    ),
    (
        "evolution_concurrence",
        "Évolution de la concurrence",
        "Marché",
        "L'offre concurrente évolue et réduit l'avantage du projet.",
        2,
    ),
]

#: Catalogue d'opportunités types (code, libellé, catégorie, description, impact 1-5).
_OPPORTUNITY_TYPES: list[tuple[str, str, str, str, int]] = [
    (
        "nouveaux_revenus",
        "Nouvelles sources de revenus",
        "Croissance",
        "Le projet ouvre des flux de revenus inédits pour le groupe.",
        4,
    ),
    (
        "reduction_couts",
        "Réduction des coûts opérationnels",
        "Efficacité",
        "Le projet génère des économies durables sur les coûts internes.",
        4,
    ),
    (
        "fidelisation_client",
        "Fidélisation client accrue",
        "Client",
        "Le service renforce la fidélité et la satisfaction des clients.",
        3,
    ),
    (
        "differentiation",
        "Différenciation concurrentielle",
        "Stratégie",
        "Le projet distingue l'offre du groupe face à la concurrence.",
        4,
    ),
    (
        "expansion_marche",
        "Expansion sur de nouveaux marchés",
        "Croissance",
        "Le projet permet d'adresser de nouveaux segments ou territoires.",
        3,
    ),
    (
        "partenariats",
        "Partenariats stratégiques",
        "Écosystème",
        "Le projet favorise des alliances créatrices de valeur.",
        3,
    ),
    (
        "valorisation_donnees",
        "Valorisation des données",
        "Innovation",
        "Le projet exploite les données pour créer de nouveaux services.",
        4,
    ),
    (
        "amelioration_rse",
        "Amélioration de l'impact RSE",
        "RSE",
        "Le projet contribue aux objectifs sociaux et environnementaux.",
        3,
    ),
    (
        "attractivite_employeur",
        "Attractivité employeur",
        "RH",
        "Le projet renforce la marque employeur et l'engagement des agents.",
        2,
    ),
    (
        "innovation_service",
        "Innovation de service",
        "Innovation",
        "Le projet introduit une innovation perceptible par les clients.",
        4,
    ),
]

#: Catalogue de paramètres stratégiques (code, libellé, dimension, description, poids 0-1).
_STRATEGIC_PARAMETERS: list[tuple[str, str, str, str, float]] = [
    (
        "roi_attendu",
        "ROI attendu à 3 ans",
        "rentabilite",
        "Retour sur investissement projeté à horizon trois ans.",
        0.35,
    ),
    (
        "marge_operationnelle",
        "Marge opérationnelle cible",
        "rentabilite",
        "Marge dégagée par l'activité une fois en régime établi.",
        0.25,
    ),
    (
        "payback",
        "Délai de retour sur investissement",
        "rentabilite",
        "Durée nécessaire pour récupérer l'investissement initial.",
        0.25,
    ),
    (
        "potentiel_revenus",
        "Potentiel de revenus récurrents",
        "rentabilite",
        "Capacité à générer des revenus récurrents et pérennes.",
        0.15,
    ),
    (
        "alignement_strategie_groupe",
        "Alignement avec la stratégie groupe",
        "alignement",
        "Cohérence du projet avec les priorités stratégiques du groupe.",
        0.35,
    ),
    (
        "coherence_portefeuille",
        "Cohérence avec le portefeuille",
        "alignement",
        "Complémentarité avec les offres et projets existants.",
        0.25,
    ),
    (
        "priorite_direction",
        "Priorité pour la direction",
        "alignement",
        "Niveau de priorité accordé par la direction porteuse.",
        0.20,
    ),
    (
        "synergie_metiers",
        "Synergies inter-métiers",
        "alignement",
        "Effets de levier entre plusieurs métiers du groupe.",
        0.20,
    ),
    (
        "risque_technologique",
        "Maîtrise du risque technologique",
        "risque",
        "Degré de maîtrise des technologies mobilisées.",
        0.30,
    ),
    (
        "risque_reglementaire",
        "Conformité réglementaire",
        "risque",
        "Capacité à respecter le cadre légal et réglementaire.",
        0.30,
    ),
    (
        "risque_marche",
        "Risque d'adoption marché",
        "risque",
        "Incertitude sur l'adoption par les utilisateurs cibles.",
        0.25,
    ),
    (
        "dependance_fournisseur",
        "Dépendance fournisseur",
        "risque",
        "Exposition à un prestataire ou éditeur critique.",
        0.15,
    ),
    (
        "gain_productivite",
        "Gain de productivité opérationnelle",
        "impact_operationnel",
        "Amélioration de la productivité des processus internes.",
        0.40,
    ),
    (
        "amelioration_qualite",
        "Amélioration de la qualité de service",
        "impact_operationnel",
        "Effet positif sur la qualité perçue du service rendu.",
        0.35,
    ),
    (
        "impact_processus",
        "Impact sur les processus internes",
        "impact_operationnel",
        "Ampleur des transformations induites sur les processus.",
        0.25,
    ),
    (
        "impact_environnemental",
        "Réduction de l'empreinte carbone",
        "impact_social",
        "Contribution à la réduction de l'empreinte environnementale.",
        0.40,
    ),
    (
        "impact_emploi",
        "Impact sur l'emploi et les compétences",
        "impact_social",
        "Effets sur l'emploi, les métiers et la montée en compétences.",
        0.35,
    ),
    (
        "inclusion_numerique",
        "Contribution à l'inclusion numérique",
        "impact_social",
        "Apport du projet à l'accès et à l'inclusion numériques.",
        0.25,
    ),
    (
        "maturite_technique",
        "Maturité technique de la solution",
        "faisabilite",
        "Niveau de maturité et d'éprouvé de la solution envisagée.",
        0.55,
    ),
    (
        "disponibilite_competences",
        "Disponibilité des compétences",
        "faisabilite",
        "Disponibilité des compétences nécessaires à la réalisation.",
        0.45,
    ),
]

#: Catalogue d'hypothèses financières types (code, libellé, catégorie, unité, valeur, description).
_FINANCIAL_HYPOTHESES: list[tuple[str, str, str, str, float, str]] = [
    (
        "inv_materiel",
        "Investissement matériel",
        "investissement",
        "EUR",
        150000,
        "Achat du matériel et des équipements nécessaires au lancement.",
    ),
    (
        "inv_logiciel",
        "Licences logicielles initiales",
        "investissement",
        "EUR",
        80000,
        "Acquisition des licences logicielles structurantes.",
    ),
    (
        "inv_dev",
        "Développement initial",
        "investissement",
        "EUR",
        200000,
        "Conception et développement de la solution.",
    ),
    (
        "inv_infra",
        "Infrastructure cloud initiale",
        "investissement",
        "EUR",
        60000,
        "Mise en place de l'infrastructure d'hébergement.",
    ),
    (
        "inv_formation",
        "Formation initiale des équipes",
        "investissement",
        "EUR",
        40000,
        "Formation des équipes à la prise en main de la solution.",
    ),
    (
        "inv_conduite_changement",
        "Conduite du changement",
        "investissement",
        "EUR",
        50000,
        "Accompagnement au changement et communication interne.",
    ),
    (
        "inv_securite",
        "Mise en conformité sécurité",
        "investissement",
        "EUR",
        35000,
        "Travaux de sécurisation et de mise en conformité initiale.",
    ),
    (
        "inv_design",
        "UX et design produit",
        "investissement",
        "EUR",
        25000,
        "Conception de l'expérience utilisateur et du design.",
    ),
    (
        "rev_abonnement",
        "Revenus d'abonnement",
        "revenu",
        "EUR/an",
        250000,
        "Revenus récurrents issus des abonnements au service.",
    ),
    (
        "rev_transaction",
        "Commissions transactionnelles",
        "revenu",
        "EUR/an",
        180000,
        "Commissions perçues sur les transactions réalisées.",
    ),
    (
        "rev_economie_couts",
        "Économies de coûts internes",
        "revenu",
        "EUR/an",
        120000,
        "Économies valorisées comme gains sur les coûts internes.",
    ),
    (
        "rev_productivite",
        "Gains de productivité valorisés",
        "revenu",
        "EUR/an",
        90000,
        "Valorisation financière des gains de productivité.",
    ),
    (
        "rev_nouveaux_clients",
        "Revenus de nouveaux clients",
        "revenu",
        "EUR/an",
        200000,
        "Revenus issus de la conquête de nouveaux clients.",
    ),
    (
        "rev_cross_sell",
        "Ventes croisées",
        "revenu",
        "EUR/an",
        75000,
        "Revenus additionnels issus de ventes croisées.",
    ),
    (
        "rev_publicite",
        "Revenus publicitaires et partenariats",
        "revenu",
        "EUR/an",
        40000,
        "Revenus issus de la publicité et des partenariats.",
    ),
    (
        "rev_subvention",
        "Subventions et aides",
        "revenu",
        "EUR/an",
        30000,
        "Aides publiques ou subventions perçues.",
    ),
    (
        "cout_personnel",
        "Coûts de personnel",
        "cout",
        "EUR/an",
        220000,
        "Charges salariales des équipes dédiées au projet.",
    ),
    (
        "cout_hebergement",
        "Hébergement et cloud récurrent",
        "cout",
        "EUR/an",
        60000,
        "Coûts récurrents d'hébergement et de cloud.",
    ),
    (
        "cout_maintenance",
        "Maintenance applicative",
        "cout",
        "EUR/an",
        70000,
        "Maintenance corrective et évolutive de la solution.",
    ),
    (
        "cout_support",
        "Support client",
        "cout",
        "EUR/an",
        45000,
        "Coûts du support et de l'assistance aux utilisateurs.",
    ),
    (
        "cout_licences",
        "Licences récurrentes",
        "cout",
        "EUR/an",
        35000,
        "Renouvellement annuel des licences logicielles.",
    ),
    (
        "cout_marketing",
        "Marketing et acquisition",
        "cout",
        "EUR/an",
        50000,
        "Dépenses de marketing et d'acquisition d'utilisateurs.",
    ),
    (
        "cout_logistique",
        "Logistique et déploiement",
        "cout",
        "EUR/an",
        40000,
        "Coûts logistiques et de déploiement sur le terrain.",
    ),
    (
        "cout_telecom",
        "Télécommunications et réseau",
        "cout",
        "EUR/an",
        20000,
        "Coûts de connectivité et de télécommunications.",
    ),
    (
        "cout_assurance",
        "Assurances et couverture des risques",
        "cout",
        "EUR/an",
        15000,
        "Primes d'assurance et couverture des risques.",
    ),
    (
        "cout_amortissement",
        "Amortissement du matériel",
        "cout",
        "EUR/an",
        30000,
        "Dotation annuelle aux amortissements du matériel.",
    ),
    (
        "delai_mise_en_marche",
        "Délai de mise en marché",
        "delai",
        "mois",
        12,
        "Durée avant la mise sur le marché du service.",
    ),
    (
        "delai_rentabilite",
        "Délai de rentabilité cible",
        "delai",
        "mois",
        30,
        "Horizon cible d'atteinte de la rentabilité.",
    ),
    (
        "duree_amortissement",
        "Durée d'amortissement",
        "delai",
        "mois",
        60,
        "Durée d'amortissement des investissements matériels.",
    ),
    (
        "delai_montee_charge",
        "Délai de montée en charge",
        "delai",
        "mois",
        9,
        "Durée nécessaire pour atteindre le volume cible.",
    ),
    (
        "delai_deploiement",
        "Délai de déploiement national",
        "delai",
        "mois",
        18,
        "Durée de généralisation à l'échelle nationale.",
    ),
    (
        "delai_pilote",
        "Durée de la phase pilote",
        "delai",
        "mois",
        6,
        "Durée de l'expérimentation pilote avant généralisation.",
    ),
    (
        "taux_actualisation",
        "Taux d'actualisation",
        "financement",
        "%",
        8,
        "Taux retenu pour l'actualisation des flux futurs.",
    ),
    (
        "taux_croissance_revenus",
        "Croissance annuelle des revenus",
        "financement",
        "%",
        10,
        "Hypothèse de croissance annuelle des revenus.",
    ),
    (
        "taux_inflation_couts",
        "Inflation des coûts",
        "financement",
        "%",
        3,
        "Hypothèse d'inflation annuelle appliquée aux coûts.",
    ),
    (
        "bfr_jours_ca",
        "BFR en jours de chiffre d'affaires",
        "financement",
        "jours",
        30,
        "Besoin en fonds de roulement exprimé en jours de CA.",
    ),
]


def seed_reference_data(session: Session) -> dict[str, int]:
    """Insère les catalogues de référence manquants (BIZ-88).

    Idempotent : une entrée déjà présente (même ``code``) n'est pas recréée.

    Args:
        session: Session SQLAlchemy active.

    Returns:
        Le nombre d'entrées créées par catalogue.
    """
    created: dict[str, int] = {
        "risk_types": 0,
        "opportunity_types": 0,
        "strategic_parameters": 0,
        "financial_hypotheses": 0,
    }

    for code, libelle, categorie, description, severite in _RISK_TYPES:
        if _missing(session, RiskType, code):
            session.add(
                RiskType(
                    code=code,
                    libelle=libelle,
                    categorie=categorie,
                    description=description,
                    severite_defaut=severite,
                )
            )
            created["risk_types"] += 1

    for code, libelle, categorie, description, impact in _OPPORTUNITY_TYPES:
        if _missing(session, OpportunityType, code):
            session.add(
                OpportunityType(
                    code=code,
                    libelle=libelle,
                    categorie=categorie,
                    description=description,
                    impact_defaut=impact,
                )
            )
            created["opportunity_types"] += 1

    for code, libelle, dimension, description, poids in _STRATEGIC_PARAMETERS:
        if _missing(session, StrategicParameter, code):
            session.add(
                StrategicParameter(
                    code=code,
                    libelle=libelle,
                    dimension=dimension,
                    description=description,
                    poids=poids,
                )
            )
            created["strategic_parameters"] += 1

    for code, libelle, categorie, unite, valeur, description in _FINANCIAL_HYPOTHESES:
        if _missing(session, FinancialHypothesis, code):
            session.add(
                FinancialHypothesis(
                    code=code,
                    libelle=libelle,
                    categorie=categorie,
                    unite=unite,
                    valeur_defaut=valeur,
                    description=description,
                )
            )
            created["financial_hypotheses"] += 1

    session.commit()
    return created


def _missing(session: Session, model: type, code: str) -> bool:
    """Indique si aucune entrée de ``model`` n'a le code donné.

    Args:
        session: Session SQLAlchemy active.
        model: Classe ORM du catalogue de référence.
        code: Code stable de l'entrée recherchée.

    Returns:
        ``True`` si l'entrée est absente, ``False`` sinon.
    """
    return (
        session.execute(select(model).where(model.code == code)).scalar_one_or_none()  # type: ignore[attr-defined]
        is None
    )


def seed() -> int:
    """Insère les projets de démonstration manquants.

    Returns:
        Le nombre de projets créés lors de cet appel.
    """
    init_db()
    created = 0
    with Session(get_engine()) as session:
        seed_reference_data(session)
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
