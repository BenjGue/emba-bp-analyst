"""Tests de l'orchestrateur de génération IA et de son repli (BIZ-14)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_engine
from app.services.generation import generate_business_plan
from tests.conftest import FakeAiClient

_FINANCIALS = {
    "investissement_initial": 100000,
    "revenus_annuels": 80000,
    "couts_annuels": 30000,
    "delai_rentabilite_mois": 36,
}
_DIMS = {
    "rentabilite": 8,
    "alignement": 7,
    "risque": 6,
    "impact_operationnel": 7,
    "impact_social": 6,
    "faisabilite": 8,
}

_REDACTEUR = {
    "resume_executif": "Résumé IA.",
    "presentation_projet": "Présentation IA.",
    "analyse_marche": "Marché IA.",
    "proposition_valeur": "Valeur IA.",
    "modele_economique": "Modèle IA.",
    "plan_operationnel": "Plan IA.",
    "analyse_risques": "Risques IA.",
    "hypotheses_financieres": "Hypothèses IA.",
    "impact_strategique": "Impact IA.",
    "recommandation": "Recommandation IA.",
}


def _agent_responder(system: str, user: str) -> str:
    """Renvoie le JSON canonique attendu selon l'agent appelé."""
    if "agent Analyste" in system:
        return json.dumps({"forces": ["f"], "faiblesses": [], "risques": ["r"], "opportunites": []})
    if "agent Financier" in system:
        return json.dumps(
            {
                "analyse_globale": "Commentaire financier IA.",
                "scenario_bas": "bas",
                "scenario_median": "median",
                "scenario_haut": "haut",
            }
        )
    if "agent Rédacteur" in system:
        return json.dumps(_REDACTEUR)
    if "agent Synthèse" in system:
        return json.dumps({"synthese_codir": "Note CODIR IA."})
    return "{}"


def _prepare(client: TestClient, project_id: int) -> None:
    client.put(f"/projects/{project_id}/financials", json=_FINANCIALS)
    client.put(f"/projects/{project_id}/dimensions", json=_DIMS)


def test_generation_ia_produit_un_bp_enrichi(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    get_settings.cache_clear()
    settings = get_settings()
    settings.ai_enabled = True
    fake = FakeAiClient(_agent_responder)
    try:
        with Session(get_engine()) as session:
            bp = generate_business_plan(session, project_id, client=fake)
            assert bp.status == "generated_ai"
            assert bp.sections["Résumé exécutif"] == "Résumé IA."
            assert "Commentaire financier IA." in bp.sections["Hypothèses et scénarios financiers"]
            assert bp.synthese_codir == "Note CODIR IA."
    finally:
        get_settings.cache_clear()


def test_generation_ia_en_echec_bascule_sur_le_deterministe(
    client: TestClient, project_id: int
) -> None:
    _prepare(client, project_id)
    get_settings.cache_clear()
    settings = get_settings()
    settings.ai_enabled = True
    fake = FakeAiClient(lambda system, user: "JSON invalide")
    try:
        with Session(get_engine()) as session:
            bp = generate_business_plan(session, project_id, client=fake)
            assert bp.status == "generated"
            assert bp.sections
    finally:
        get_settings.cache_clear()


def test_generation_ia_desactivee_reste_deterministe(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    with Session(get_engine()) as session:
        bp = generate_business_plan(session, project_id)
        assert bp.status == "generated"
        assert bp.sections
