"""Service de génération du business plan (EPIC 3, BIZ-14).

Le service orchestre la génération du business plan. Deux modes coexistent :

* **Mode IA** (``ai_enabled`` actif) : une chaîne d'agents (Analyste, Financier,
  Rédacteur, Synthèse) rédige le contenu via Azure AI Foundry.
* **Mode déterministe** (repli) : un contenu template est produit à partir des
  seules données saisies, sans appel externe.

Garde-fou clé : les **chiffres financiers** (scénarios, ROI, retour sur
investissement) et le **score** restent calculés par le backend. L'IA rédige et
commente, elle ne calcule jamais. En cas d'échec IA, le service retombe
automatiquement sur le mode déterministe afin de toujours produire un livrable.
"""

from __future__ import annotations

import logging
from typing import Final

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import BusinessPlan, Project, Scenario
from app.schemas.ai import AnalysteOutput, FinancierOutput, RedacteurOutput
from app.services.ai import agents
from app.services.ai.client import AiClient, get_ai_client
from app.services.ai.errors import AiError
from app.services.financials import get_financials
from app.services.projects import get_project

logger = logging.getLogger("bizplan.generation")

#: Variation appliquée aux revenus pour les scénarios bas / médian / haut.
_SCENARIO_FACTORS: Final[dict[str, float]] = {
    "bas": 0.8,
    "median": 1.0,
    "haut": 1.2,
}

#: Hypothèse de besoin en fonds de roulement : nombre de jours de chiffre
#: d'affaires immobilisés (créances clients nettes des dettes fournisseurs).
_BFR_JOURS_CA: Final[int] = 30

#: Correspondance clé schéma Rédacteur -> titre de section affiché.
_SECTION_TITLES: Final[dict[str, str]] = {
    "resume_executif": "Résumé exécutif",
    "presentation_projet": "Présentation du projet",
    "analyse_marche": "Analyse du marché et du contexte",
    "analyse_concurrentielle": "Analyse concurrentielle",
    "proposition_valeur": "Proposition de valeur",
    "modele_economique": "Modèle économique",
    "plan_operationnel": "Plan opérationnel",
    "analyse_risques": "Analyse des risques",
    "hypotheses_financieres": "Hypothèses et scénarios financiers",
    "impact_strategique": "Impact stratégique et RSE",
    "recommandation": "Recommandation et prochaines étapes",
}


def _scenario_payback(
    delai_rentabilite_mois: int,
    resultat_median: float,
    resultat: float,
    investissement: float,
) -> float:
    """Calcule le délai de retour sur investissement d'un scénario (mois).

    Le délai de référence (``delai_rentabilite_mois``) provient des données
    financières : il est dérivé du profil mensuel réel lors d'un import détaillé
    (premier mois où la trésorerie cumulée redevient positive) ou saisi
    directement. Il sert de payback du scénario médian. Les scénarios bas et
    haut le mettent à l'échelle selon le ratio de résultat net, le délai étant
    inversement proportionnel au résultat. Un repli analytique annualisé est
    utilisé si le délai de référence n'est pas exploitable.

    Args:
        delai_rentabilite_mois: Délai de rentabilité de référence (médian).
        resultat_median: Résultat net annuel du scénario médian (€).
        resultat: Résultat net annuel du scénario courant (€).
        investissement: Investissement initial (€).

    Returns:
        Le délai de retour (mois), ou ``-1.0`` si le projet n'est jamais rentable.
    """
    if resultat <= 0:
        return -1.0
    if delai_rentabilite_mois > 0 and resultat_median > 0:
        return round(min(600.0, delai_rentabilite_mois * (resultat_median / resultat)), 1)
    # Repli analytique annualisé lorsqu'aucun délai de référence n'est exploitable.
    return round(investissement / resultat * 12, 1) if investissement else -1.0


def _build_scenarios(
    investissement: float,
    revenus: float,
    couts: float,
    delai_rentabilite_mois: int,
) -> dict[str, dict[str, float]]:
    """Calcule les scénarios financiers à partir des hypothèses.

    Args:
        investissement: Investissement initial (€).
        revenus: Revenus annuels de référence (€).
        couts: Coûts annuels d'exploitation (€).
        delai_rentabilite_mois: Délai de rentabilité de référence (mois), issu
            des données financières (import détaillé ou saisie). Sert de payback
            du scénario médian afin de rester cohérent avec l'horizon réel.

    Returns:
        Pour chaque scénario, les revenus, coûts, résultat net annuel, ROI,
        délai de retour sur investissement (mois), besoin en fonds de roulement
        estimé et trésorerie de fin de première année (€).
    """
    resultat_median = round(revenus - couts, 2)
    scenarios: dict[str, dict[str, float]] = {}
    for name, factor in _SCENARIO_FACTORS.items():
        revenus_scenario = round(revenus * factor, 2)
        resultat = round(revenus_scenario - couts, 2)
        roi = round((resultat / investissement * 100) if investissement else 0.0, 2)
        payback = _scenario_payback(
            delai_rentabilite_mois, resultat_median, resultat, investissement
        )
        # BFR estimé : part du chiffre d'affaires immobilisée (jours de CA).
        bfr = round(revenus_scenario / 360 * _BFR_JOURS_CA, 2)
        # Trésorerie de fin d'année 1 : résultat net diminué de l'investissement
        # initial et du besoin en fonds de roulement à financer.
        tresorerie = round(resultat - investissement - bfr, 2)
        scenarios[name] = {
            "revenus_annuels": revenus_scenario,
            "couts_annuels": round(couts, 2),
            "resultat_net_annuel": resultat,
            "roi_pourcent": roi,
            "retour_investissement_mois": payback,
            "bfr_estime": bfr,
            "tresorerie_fin_annee": tresorerie,
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
        "Analyse concurrentielle": (
            "Positionnement face aux alternatives internes et aux solutions du "
            f"marché sur le périmètre de la direction {project.direction} "
            "(analyse détaillée générée par l'IA)."
        ),
        "Proposition de valeur": (
            "Synthèse de la valeur créée pour les parties prenantes internes "
            "et les clients de La Poste (contenu détaillé généré par l'IA)."
        ),
        "Modèle économique": (
            f"Revenus annuels de référence : "
            f"{median['revenus_annuels']:.0f} € ; coûts annuels : "
            f"{median['couts_annuels']:.0f} €. Besoin en fonds de roulement "
            f"estimé ({_BFR_JOURS_CA} j de CA) : {median['bfr_estime']:.0f} € ; "
            f"trésorerie de fin de 1ʳᵉ année : {median['tresorerie_fin_annee']:.0f} €."
        ),
        "Plan opérationnel": (
            f"Déploiement planifié sur {project.duree_estimee_mois} mois, "
            "jalonné par phases (cadrage, pilote, généralisation)."
        ),
        "Analyse des risques": (
            "Cartographie des risques à enrichir par l'agent Analyste. Les "
            "risques majeurs sont suivis et provisionnés, et des actions "
            "correctives sont définies pour chacun."
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


def _bullets(items: list[str]) -> str:
    """Met en forme une liste de points en Markdown.

    Args:
        items: Éléments à lister.

    Returns:
        Une liste Markdown, ou une chaîne vide si aucun élément.
    """
    return "\n".join(f"- {item}" for item in items if item)


def _build_sections_from_ai(
    redacteur: RedacteurOutput,
    analyse: AnalysteOutput,
    financier: FinancierOutput,
) -> dict[str, str]:
    """Assemble les sections affichées à partir des sorties des agents IA.

    Les 10 sections rédigées par l'agent Rédacteur sont enrichies par la
    cartographie des risques de l'agent Analyste et le commentaire qualitatif de
    l'agent Financier, en conservant les titres de sections existants (l'export
    et l'UI restent inchangés).

    Args:
        redacteur: Sections rédactionnelles produites par l'agent Rédacteur.
        analyse: Analyse stratégique produite par l'agent Analyste.
        financier: Commentaire financier produit par l'agent Financier.

    Returns:
        Un dictionnaire ``titre de section -> contenu Markdown``.
    """
    fields = redacteur.model_dump()
    sections = {title: fields[key] for key, title in _SECTION_TITLES.items()}

    risques = _bullets(analyse.risques)
    if risques:
        sections["Analyse des risques"] = (
            f"{sections['Analyse des risques']}\n\n**Risques identifiés :**\n{risques}"
        )

    actions = _bullets(analyse.actions_correctives)
    if actions:
        sections["Analyse des risques"] = (
            f"{sections['Analyse des risques']}\n\n**Actions correctives :**\n{actions}"
        )

    commentaire = financier.analyse_globale.strip()
    if commentaire:
        sections["Hypothèses et scénarios financiers"] = (
            f"{sections['Hypothèses et scénarios financiers']}\n\n{commentaire}"
        )
    return sections


def _generate_with_ai(
    project: Project,
    scenarios: dict[str, dict[str, float]],
    score_total: float | None,
    client: AiClient,
) -> tuple[dict[str, str], str]:
    """Génère le contenu du business plan via la chaîne d'agents IA.

    Args:
        project: Projet source.
        scenarios: Scénarios financiers calculés par le backend.
        score_total: Score de pertinence calculé (0-100) ou ``None``.
        client: Client IA injecté.

    Returns:
        Le couple ``(sections, synthèse CODIR)``.

    Raises:
        AiError: Si l'un des agents échoue (déclenche le repli déterministe).
    """
    analyse = agents.run_analyste(
        nom=project.nom,
        description=project.description,
        direction=project.direction,
        duree_estimee_mois=project.duree_estimee_mois,
        client=client,
    )
    financier = agents.run_financier(scenarios=scenarios, client=client)
    redacteur = agents.run_redacteur(
        nom=project.nom,
        description=project.description,
        direction=project.direction,
        duree_estimee_mois=project.duree_estimee_mois,
        score_total=score_total,
        scenarios=scenarios,
        analyse=analyse,
        client=client,
    )
    synthese = agents.run_synthese(
        nom=project.nom,
        direction=project.direction,
        score_total=score_total,
        resume_executif=redacteur.resume_executif,
        recommandation=redacteur.recommandation,
        client=client,
    )
    sections = _build_sections_from_ai(redacteur, analyse, financier)
    return sections, synthese.synthese_codir


def _generate_content(
    project: Project,
    scenarios: dict[str, dict[str, float]],
    score_total: float | None,
    settings: Settings,
    client: AiClient | None,
) -> tuple[dict[str, str], str, str]:
    """Sélectionne le mode de génération (IA ou déterministe) avec repli.

    Args:
        project: Projet source.
        scenarios: Scénarios financiers calculés.
        score_total: Score de pertinence calculé (0-100) ou ``None``.
        settings: Configuration applicative (flag ``ai_enabled``).
        client: Client IA optionnel (construit au besoin si l'IA est active).

    Returns:
        Le triplet ``(sections, synthèse, statut)``. Le statut vaut
        ``"generated_ai"`` en mode IA, ``"generated"`` en mode déterministe.
    """
    if settings.ai_enabled:
        try:
            resolved = client or get_ai_client(settings)
            sections, synthese = _generate_with_ai(project, scenarios, score_total, resolved)
            return sections, synthese, "generated_ai"
        except AiError as exc:
            # Repli déterministe : on garantit toujours un livrable.
            logger.warning("Génération IA en échec, repli déterministe : %s", exc)

    sections = _build_sections(project, scenarios, score_total)
    synthese = _build_synthese_codir(project, score_total)
    return sections, synthese, "generated"


def generate_business_plan(
    db: Session,
    project_id: int,
    *,
    client: AiClient | None = None,
) -> BusinessPlan:
    """Génère le business plan d'un projet (mode IA ou déterministe).

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet à traiter.
        client: Client IA optionnel (injecté en test ; sinon construit selon la
            configuration lorsque l'IA est active).

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
        financials.delai_rentabilite_mois,
    )
    score_total = project.scores[-1].total if project.scores else None

    sections, synthese, bp_status = _generate_content(
        project, scenarios, score_total, get_settings(), client
    )

    # Remplace un BP / des scénarios existants pour rester idempotent.
    if project.business_plan is not None:
        db.delete(project.business_plan)
    for existing in list(project.scenarios):
        db.delete(existing)
    db.flush()

    business_plan = BusinessPlan(
        project_id=project_id,
        status=bp_status,
        sections=sections,
        synthese_codir=synthese,
    )
    db.add(business_plan)
    for name, data in scenarios.items():
        db.add(Scenario(project_id=project_id, type=name, data=data))

    db.commit()
    db.refresh(business_plan)
    return business_plan
