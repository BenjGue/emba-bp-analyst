"""Tests des agents IA de génération (BIZ-15 à BIZ-18)."""

from __future__ import annotations

import json

import pytest

from app.schemas.ai import AnalysteOutput
from app.services.ai import agents
from app.services.ai.errors import AiResponseError
from tests.conftest import FakeAiClient

_SCENARIOS = {
    "bas": {"revenus_annuels": 64000.0, "resultat_net_annuel": 34000.0},
    "median": {"revenus_annuels": 80000.0, "resultat_net_annuel": 50000.0},
    "haut": {"revenus_annuels": 96000.0, "resultat_net_annuel": 66000.0},
}


def test_extract_json_retire_les_delimiteurs_markdown() -> None:
    brut = '```json\n{"forces": ["a"]}\n```'
    assert json.loads(agents._extract_json(brut)) == {"forces": ["a"]}


def test_run_analyste_parse_le_json() -> None:
    payload = {
        "forces": ["solide"],
        "faiblesses": ["coûteux"],
        "risques": ["délai"],
        "opportunites": ["marché"],
    }
    fake = FakeAiClient(lambda system, user: json.dumps(payload))
    result = agents.run_analyste(
        nom="P", description="D", direction="Numérique", duree_estimee_mois=12, client=fake
    )
    assert result.forces == ["solide"]
    assert result.risques == ["délai"]


def test_run_financier_parse_le_json() -> None:
    payload = {
        "analyse_globale": "Rentable",
        "scenario_bas": "prudent",
        "scenario_median": "réaliste",
        "scenario_haut": "ambitieux",
    }
    fake = FakeAiClient(lambda system, user: json.dumps(payload))
    result = agents.run_financier(scenarios=_SCENARIOS, client=fake)
    assert result.analyse_globale == "Rentable"


def test_run_redacteur_parse_les_sections() -> None:
    payload = {"resume_executif": "résumé", "recommandation": "Go"}
    fake = FakeAiClient(lambda system, user: json.dumps(payload))
    result = agents.run_redacteur(
        nom="P",
        description="D",
        direction="Numérique",
        duree_estimee_mois=12,
        score_total=75.0,
        scenarios=_SCENARIOS,
        analyse=AnalysteOutput(),
        client=fake,
    )
    assert result.resume_executif == "résumé"
    assert result.recommandation == "Go"


def test_run_synthese_parse_le_json() -> None:
    fake = FakeAiClient(lambda system, user: json.dumps({"synthese_codir": "Note CODIR"}))
    result = agents.run_synthese(
        nom="P",
        direction="Numérique",
        score_total=75.0,
        resume_executif="résumé",
        recommandation="Go",
        client=fake,
    )
    assert result.synthese_codir == "Note CODIR"


def test_agent_json_invalide_leve_ai_response_error() -> None:
    fake = FakeAiClient(lambda system, user: "ceci n'est pas du JSON")
    with pytest.raises(AiResponseError):
        agents.run_analyste(
            nom="P", description="D", direction="Numérique", duree_estimee_mois=12, client=fake
        )
