"""Agents IA de génération du business plan (EPIC 3, BIZ-15 à BIZ-18).

Chaque agent encapsule un appel au modèle (prompt système dédié, réponse JSON)
puis valide la sortie via un schéma Pydantic. Conformément au principe « l'IA
rédige et raisonne, le backend valide et calcule », aucun agent ne produit de
chiffre financier ni de score : ces valeurs sont calculées par le backend et
seulement commentées par l'IA.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from app.schemas.ai import (
    AnalysteOutput,
    EvaluateurOutput,
    FinancierOutput,
    RedacteurOutput,
    SyntheseOutput,
)
from app.services.ai.client import AiClient
from app.services.ai.errors import AiResponseError
from app.services.ai.prompts import (
    ANALYSTE_SYSTEM,
    EVALUATEUR_SYSTEM,
    FINANCIER_SYSTEM,
    REDACTEUR_SYSTEM,
    SYNTHESE_SYSTEM,
)


def _extract_json(text: str) -> str:
    """Isole le bloc JSON d'une réponse, en retirant d'éventuels délimiteurs.

    Certains modèles encadrent le JSON par des balises Markdown (```json ...```).
    Cette fonction extrait le contenu situé entre la première accolade ouvrante
    et la dernière accolade fermante.

    Args:
        text: Réponse brute du modèle.

    Returns:
        La sous-chaîne supposée contenir le JSON.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return text
    return text[start : end + 1]


def _parse[TModel: BaseModel](text: str, model: type[TModel]) -> TModel:
    """Valide une réponse JSON contre un schéma Pydantic.

    Args:
        text: Réponse brute du modèle.
        model: Classe de schéma cible.

    Returns:
        L'instance validée du schéma.

    Raises:
        AiResponseError: Si la réponse n'est pas un JSON conforme au schéma.
    """
    try:
        payload = json.loads(_extract_json(text))
        return model.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise AiResponseError(f"Réponse IA non conforme à {model.__name__}.") from exc


def run_analyste(
    *,
    nom: str,
    description: str,
    direction: str,
    duree_estimee_mois: int,
    client: AiClient,
) -> AnalysteOutput:
    """Produit l'analyse stratégique du projet (BIZ-15).

    Args:
        nom: Nom du projet.
        description: Description du projet.
        direction: Direction concernée.
        duree_estimee_mois: Horizon temporel estimé.
        client: Client IA injecté.

    Returns:
        Forces, faiblesses, risques et opportunités identifiés.

    Raises:
        AiResponseError: Si la réponse est non exploitable.
    """
    user = (
        f"Projet : {nom}\nDirection : {direction}\n"
        f"Durée estimée : {duree_estimee_mois} mois\nDescription : {description}"
    )
    completion = client.complete(system=ANALYSTE_SYSTEM, user=user, json_mode=True)
    return _parse(completion.text, AnalysteOutput)


def run_evaluateur(
    *,
    nom: str,
    description: str,
    direction: str,
    duree_estimee_mois: int,
    financials: dict[str, float] | None,
    client: AiClient,
) -> EvaluateurOutput:
    """Propose les 6 notes stratégiques à partir des données du projet (BIZ-56).

    L'IA déduit les notes des informations saisies en partie A et fournit une
    justification par dimension ainsi qu'une synthèse globale. Les notes sont
    validées et bornées ensuite côté backend.

    Args:
        nom: Nom du projet.
        description: Description du projet.
        direction: Direction concernée.
        duree_estimee_mois: Horizon temporel estimé.
        financials: Hypothèses financières clés déjà saisies, ou ``None``.
        client: Client IA injecté.

    Returns:
        Les notes proposées, leurs justifications et la synthèse.

    Raises:
        AiResponseError: Si la réponse est non exploitable.
    """
    finance_txt = json.dumps(financials, ensure_ascii=False) if financials else "non renseignées"
    user = (
        f"Projet : {nom}\nDirection : {direction}\n"
        f"Durée estimée : {duree_estimee_mois} mois\n"
        f"Données financières (calculées par le backend) : {finance_txt}\n"
        f"Description : {description}"
    )
    completion = client.complete(system=EVALUATEUR_SYSTEM, user=user, json_mode=True)
    return _parse(completion.text, EvaluateurOutput)


def run_financier(
    *,
    scenarios: dict[str, dict[str, float]],
    client: AiClient,
) -> FinancierOutput:
    """Commente les scénarios financiers calculés par le backend (BIZ-16).

    Args:
        scenarios: Scénarios financiers déjà calculés (bas, médian, haut).
        client: Client IA injecté.

    Returns:
        Le commentaire qualitatif des scénarios.

    Raises:
        AiResponseError: Si la réponse est non exploitable.
    """
    user = (
        "Voici les scénarios financiers déjà calculés (ne pas recalculer, "
        "seulement commenter) :\n" + json.dumps(scenarios, ensure_ascii=False)
    )
    completion = client.complete(system=FINANCIER_SYSTEM, user=user, json_mode=True)
    return _parse(completion.text, FinancierOutput)


def run_redacteur(
    *,
    nom: str,
    description: str,
    direction: str,
    duree_estimee_mois: int,
    score_total: float | None,
    scenarios: dict[str, dict[str, float]],
    analyse: AnalysteOutput,
    client: AiClient,
) -> RedacteurOutput:
    """Rédige les 11 sections du business plan (BIZ-17).

    Args:
        nom: Nom du projet.
        description: Description du projet.
        direction: Direction concernée.
        duree_estimee_mois: Horizon temporel estimé.
        score_total: Score de pertinence calculé (0-100) ou ``None``.
        scenarios: Scénarios financiers calculés.
        analyse: Analyse stratégique produite par l'agent Analyste.
        client: Client IA injecté.

    Returns:
        Les sections rédactionnelles du business plan.

    Raises:
        AiResponseError: Si la réponse est non exploitable.
    """
    score_txt = f"{score_total:.0f}/100" if score_total is not None else "non calculé"
    user = (
        f"Projet : {nom}\nDirection : {direction}\n"
        f"Durée estimée : {duree_estimee_mois} mois\n"
        f"Score de pertinence (calculé par le backend) : {score_txt}\n"
        f"Description : {description}\n"
        f"Analyse stratégique : {analyse.model_dump_json()}\n"
        f"Scénarios financiers (calculés) : {json.dumps(scenarios, ensure_ascii=False)}"
    )
    completion = client.complete(system=REDACTEUR_SYSTEM, user=user, json_mode=True)
    return _parse(completion.text, RedacteurOutput)


def run_synthese(
    *,
    nom: str,
    direction: str,
    score_total: float | None,
    resume_executif: str,
    recommandation: str,
    client: AiClient,
) -> SyntheseOutput:
    """Rédige la note de synthèse CODIR (BIZ-18).

    Args:
        nom: Nom du projet.
        direction: Direction concernée.
        score_total: Score de pertinence calculé (0-100) ou ``None``.
        resume_executif: Résumé exécutif produit par l'agent Rédacteur.
        recommandation: Recommandation produite par l'agent Rédacteur.
        client: Client IA injecté.

    Returns:
        La note de synthèse à destination du CODIR.

    Raises:
        AiResponseError: Si la réponse est non exploitable.
    """
    score_txt = f"{score_total:.0f}/100" if score_total is not None else "non calculé"
    user = (
        f"Projet : {nom}\nDirection : {direction}\n"
        f"Score de pertinence : {score_txt}\n"
        f"Résumé exécutif : {resume_executif}\n"
        f"Recommandation : {recommandation}"
    )
    completion = client.complete(system=SYNTHESE_SYSTEM, user=user, json_mode=True)
    return _parse(completion.text, SyntheseOutput)
