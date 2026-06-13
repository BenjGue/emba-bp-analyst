"""Service de génération du business plan — version MOCKÉE (US-3.x différée).

La génération multi-agents IA (EPIC 3, BIZ-14 à BIZ-18) est différée. Ce service
produit un business plan **déterministe** à partir des données saisies (projet,
hypothèses financières, score) afin de débloquer la consultation (US-4.1) et
l'export (US-4.2). Aucune donnée n'est inventée : les chiffres dérivent
strictement des hypothèses fournies.

À remplacer ultérieurement par l'orchestration Azure AI Foundry.
"""

from __future__ import annotations

from typing import Final

from sqlalchemy.orm import Session

from app.models import BusinessPlan, Project, Scenario
from app.services.financials import get_financials
from app.services.projects import get_project

#: Variation appliquée aux revenus pour les scénarios bas / médian / haut.
_SCENARIO_FACTORS: Final[dict[str, float]] = {
    "bas": 0.8,
    "median": 1.0,
    "haut": 1.2,
}


def _build_scenarios(
    investissement: float,
    revenus: float,
    couts: float,
) -> dict[str, dict[str, float]]:
    """Calcule les scénarios financiers à partir des hypothèses.

    Args:
        investissement: Investissement initial (€).
        revenus: Revenus annuels de référence (€).
        couts: Coûts annuels d'exploitation (€).

    Returns:
        Pour chaque scénario, les revenus, coûts, résultat net annuel, ROI et
        délai de retour sur investissement (mois).
    """
    scenarios: dict[str, dict[str, float]] = {}
    for name, factor in _SCENARIO_FACTORS.items():
        revenus_scenario = round(revenus * factor, 2)
        resultat = round(revenus_scenario - couts, 2)
        roi = round((resultat / investissement * 100) if investissement else 0.0, 2)
        payback = round(investissement / resultat * 12, 1) if resultat > 0 else -1.0
        scenarios[name] = {
            "revenus_annuels": revenus_scenario,
            "couts_annuels": round(couts, 2),
            "resultat_net_annuel": resultat,
            "roi_pourcent": roi,
            "retour_investissement_mois": payback,
        }
    return scenarios


def _build_sections(
    project: Project,
    scenarios: dict[str, dict[str, float]],
    score_total: float | None,
) -> dict[str, str]:
    """Construit le contenu Markdown des sections du business plan.

    Args:
        project: Projet source.
        scenarios: Scénarios financiers calculés.
        score_total: Score de pertinence (0-100) ou ``None``.

    Returns:
        Un dictionnaire ``titre de section -> contenu Markdown``.
    """
    median = scenarios["median"]
    score_txt = f"{score_total:.0f}/100" if score_total is not None else "non calculé"
    contents: dict[str, str] = {
        "Résumé exécutif": (
            f"Le projet **{project.nom}** porté par la direction "
            f"{project.direction} vise à {project.description.lower()} "
            f"Score de pertinence : {score_txt}. Résultat net annuel médian "
            f"estimé : {median['resultat_net_annuel']:.0f} €."
        ),
        "Présentation du projet": (
            f"{project.description}\n\nHorizon de mise en œuvre estimé : "
            f"{project.duree_estimee_mois} mois."
        ),
        "Analyse du marché et du contexte": (
            "Analyse de marché à produire par l'agent Analyste (génération IA "
            "différée). Le cadre de référence repose sur le périmètre de la "
            f"direction {project.direction}."
        ),
        "Proposition de valeur": (
            "Synthèse de la valeur créée pour les parties prenantes internes "
            "et les clients de La Poste (contenu détaillé généré par l'IA)."
        ),
        "Modèle économique": (
            f"Revenus annuels de référence : "
            f"{median['revenus_annuels']:.0f} € ; coûts annuels : "
            f"{median['couts_annuels']:.0f} €."
        ),
        "Plan opérationnel": (
            f"Déploiement planifié sur {project.duree_estimee_mois} mois, "
            "jalonné par phases (cadrage, pilote, généralisation)."
        ),
        "Analyse des risques": (
            "Cartographie des risques à enrichir par l'agent Analyste. Les "
            "risques majeurs sont suivis et provisionnés."
        ),
        "Hypothèses et scénarios financiers": (
            "Trois scénarios sont modélisés (bas, médian, haut) à partir des "
            "hypothèses financières saisies. ROI médian : "
            f"{median['roi_pourcent']:.1f} %."
        ),
        "Impact stratégique et RSE": (
            f"Contribution aux objectifs de la direction {project.direction} "
            "et à la trajectoire RSE du groupe."
        ),
        "Recommandation et prochaines étapes": (_recommendation(score_total)),
    }
    return contents


def _recommendation(score_total: float | None) -> str:
    """Retourne une recommandation cohérente avec le score (règle métier).

    Args:
        score_total: Score de pertinence (0-100) ou ``None``.

    Returns:
        Le texte de recommandation.
    """
    if score_total is None:
        return "Score non calculé : compléter l'évaluation stratégique."
    if score_total >= 70:
        return (
            "Recommandation : **Go**. Le projet présente une pertinence élevée ; "
            "lancer la phase de cadrage détaillé."
        )
    if score_total >= 40:
        return (
            "Recommandation : **Go conditionnel**. Pertinence moyenne ; lever les "
            "réserves identifiées avant engagement."
        )
    return (
        "Recommandation : **No-Go en l'état**. Pertinence faible ; revoir les "
        "hypothèses ou le périmètre."
    )


def _build_synthese_codir(project: Project, score_total: float | None) -> str:
    """Construit la note de synthèse CODIR (une page).

    Args:
        project: Projet source.
        score_total: Score de pertinence (0-100) ou ``None``.

    Returns:
        Le texte de la note de synthèse.
    """
    score_txt = f"{score_total:.0f}/100" if score_total is not None else "non calculé"
    return (
        f"# Note de synthèse CODIR — {project.nom}\n\n"
        f"**Direction :** {project.direction}\n\n"
        f"**Score de pertinence :** {score_txt}\n\n"
        f"{project.description}\n\n"
        f"{_recommendation(score_total)}"
    )


def generate_business_plan(db: Session, project_id: int) -> BusinessPlan:
    """Génère (de façon déterministe) le business plan d'un projet.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet à traiter.

    Returns:
        Le business plan persisté, avec ses sections et scénarios.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
        FinancialsNotFoundError: Si les hypothèses financières sont absentes.
    """
    project = get_project(db, project_id)
    financials = get_financials(db, project_id)

    scenarios = _build_scenarios(
        financials.investissement_initial,
        financials.revenus_annuels,
        financials.couts_annuels,
    )
    score_total = project.scores[-1].total if project.scores else None
    sections = _build_sections(project, scenarios, score_total)
    synthese = _build_synthese_codir(project, score_total)

    # Remplace un BP / des scénarios existants pour rester idempotent.
    if project.business_plan is not None:
        db.delete(project.business_plan)
    for existing in list(project.scenarios):
        db.delete(existing)
    db.flush()

    business_plan = BusinessPlan(
        project_id=project_id,
        status="generated",
        sections=sections,
        synthese_codir=synthese,
    )
    db.add(business_plan)
    for name, data in scenarios.items():
        db.add(Scenario(project_id=project_id, type=name, data=data))

    db.commit()
    db.refresh(business_plan)
    return business_plan
