"""Tests de l'évaluation stratégique et de la consultation du score (US-1.3, US-2.3)."""

from __future__ import annotations

from fastapi.testclient import TestClient

_MAX = {
    "rentabilite": 10,
    "alignement": 10,
    "risque": 10,
    "impact_operationnel": 10,
    "impact_social": 10,
    "faisabilite": 10,
}


def test_upsert_dimensions_retourne_le_score(client: TestClient, project_id: int) -> None:
    response = client.put(f"/projects/{project_id}/dimensions", json=_MAX)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 100.0
    assert body["dimensions"]["rentabilite"]["note"] == 10


def test_read_score_apres_evaluation_retourne_200(client: TestClient, project_id: int) -> None:
    client.put(f"/projects/{project_id}/dimensions", json=_MAX)
    response = client.get(f"/projects/{project_id}/score")
    assert response.status_code == 200
    assert response.json()["total"] == 100.0


def test_read_score_sans_evaluation_retourne_404(client: TestClient, project_id: int) -> None:
    response = client.get(f"/projects/{project_id}/score")
    assert response.status_code == 404


def test_upsert_dimensions_projet_inexistant_retourne_404(
    client: TestClient,
) -> None:
    response = client.put("/projects/99999/dimensions", json=_MAX)
    assert response.status_code == 404


def test_upsert_dimensions_note_hors_bornes_retourne_422(
    client: TestClient, project_id: int
) -> None:
    invalid = {**_MAX, "rentabilite": 11}
    response = client.put(f"/projects/{project_id}/dimensions", json=invalid)
    assert response.status_code == 422
