"""Tests de la proposition assistée par IA des notes stratégiques (BIZ-56)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import StrategicAssessment
from tests.conftest import FakeAiClient

_VALID_OUTPUT = {
    "rentabilite": 7,
    "alignement": 8,
    "risque": 6,
    "impact_operationnel": 5,
    "impact_social": 4,
    "faisabilite": 9,
    "justifications": {
        "rentabilite": "Marché porteur.",
        "alignement": "Aligné avec la stratégie numérique.",
        "risque": "Risque maîtrisé.",
        "impact_operationnel": "Impact modéré.",
        "impact_social": "Bénéfice social limité.",
        "faisabilite": "Techniquement réalisable.",
    },
    "synthese": "Projet pertinent, bien aligné et faisable.",
}


def _install_fake(client: TestClient, text: str) -> FakeAiClient:
    """Installe un faux client IA via l'override de dépendance FastAPI."""
    from app.services.ai.deps import get_ai_dependency

    fake = FakeAiClient(lambda system, user: text)
    client.app.dependency_overrides[get_ai_dependency] = lambda: fake
    return fake


def test_suggest_dimensions_retourne_les_notes_proposees(
    client: TestClient, project_id: int
) -> None:
    _install_fake(client, json.dumps(_VALID_OUTPUT))
    response = client.post(f"/projects/{project_id}/dimensions/suggest")
    assert response.status_code == 200
    body = response.json()
    assert body["dimensions"]["rentabilite"] == 7
    assert body["dimensions"]["faisabilite"] == 9
    assert body["justifications"]["alignement"] == "Aligné avec la stratégie numérique."
    assert body["synthese"] == "Projet pertinent, bien aligné et faisable."
    assert body["score"]["total"] > 0


def test_suggest_dimensions_borne_les_notes_hors_intervalle(
    client: TestClient, project_id: int
) -> None:
    out = {**_VALID_OUTPUT, "rentabilite": 15, "impact_social": -3}
    _install_fake(client, json.dumps(out))
    response = client.post(f"/projects/{project_id}/dimensions/suggest")
    assert response.status_code == 200
    body = response.json()
    assert body["dimensions"]["rentabilite"] == 10
    assert body["dimensions"]["impact_social"] == 0


def test_suggest_dimensions_ia_desactivee_retourne_503(client: TestClient, project_id: int) -> None:
    response = client.post(f"/projects/{project_id}/dimensions/suggest")
    assert response.status_code == 503


def test_suggest_dimensions_projet_inexistant_retourne_404(client: TestClient) -> None:
    _install_fake(client, json.dumps(_VALID_OUTPUT))
    response = client.post("/projects/99999/dimensions/suggest")
    assert response.status_code == 404


def test_suggest_dimensions_reponse_ia_invalide_retourne_502(
    client: TestClient, project_id: int
) -> None:
    _install_fake(client, "ceci n'est pas du JSON")
    response = client.post(f"/projects/{project_id}/dimensions/suggest")
    assert response.status_code == 502


def test_upsert_dimensions_conserve_audit_ia(client: TestClient, project_id: int) -> None:
    payload = {
        "rentabilite": 7,
        "alignement": 8,
        "risque": 6,
        "impact_operationnel": 5,
        "impact_social": 4,
        "faisabilite": 9,
        "ai_synthese": "Synthèse de la logique IA.",
        "justification": "Note de faisabilité relevée après revue technique.",
    }
    response = client.put(f"/projects/{project_id}/dimensions", json=payload)
    assert response.status_code == 200

    with Session(get_engine()) as session:
        assessment = session.query(StrategicAssessment).filter_by(project_id=project_id).one()
        assert assessment.ai_synthese == "Synthèse de la logique IA."
        assert assessment.user_justification == (
            "Note de faisabilité relevée après revue technique."
        )
