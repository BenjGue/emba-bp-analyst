"""Tests du scoring rattaché à un projet (US-2.2, ``POST /projects/{id}/score``)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Score

_DIMENSIONS = {
    "rentabilite": 8,
    "alignement": 6,
    "risque": 5,
    "impact_operationnel": 7,
    "impact_social": 4,
    "faisabilite": 9,
}


def test_score_project_returns_200_with_total(client: TestClient, project_id: int) -> None:
    """Un projet existant renvoie 200 avec le score global et le détail."""
    response = client.post(f"/projects/{project_id}/score", json=_DIMENSIONS)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 66.0
    assert set(body["dimensions"]) == set(_DIMENSIONS)


def test_score_project_persists_score(client: TestClient, project_id: int) -> None:
    """Le score calculé est persisté en base, rattaché au projet."""
    client.post(f"/projects/{project_id}/score", json=_DIMENSIONS)

    with Session(get_engine()) as session:
        scores = session.execute(select(Score)).scalars().all()

    assert len(scores) == 1
    assert scores[0].project_id == project_id
    assert scores[0].total == 66.0
    assert scores[0].dimensions["rentabilite"]["contribution"] == 24.0


def test_score_project_unknown_returns_404(client: TestClient) -> None:
    """Un projet inexistant renvoie 404 et ne persiste rien."""
    response = client.post("/projects/9999/score", json=_DIMENSIONS)

    assert response.status_code == 404
    with Session(get_engine()) as session:
        assert session.execute(select(Score)).scalars().first() is None


def test_score_project_missing_dimension_returns_422(client: TestClient, project_id: int) -> None:
    """Une dimension manquante renvoie une erreur de validation 422."""
    payload = {k: v for k, v in _DIMENSIONS.items() if k != "faisabilite"}

    response = client.post(f"/projects/{project_id}/score", json=payload)

    assert response.status_code == 422


def test_score_project_out_of_range_returns_422(client: TestClient, project_id: int) -> None:
    """Une note hors de [0, 10] renvoie une erreur de validation 422."""
    payload = {**_DIMENSIONS, "rentabilite": 11}

    response = client.post(f"/projects/{project_id}/score", json=payload)

    assert response.status_code == 422


def test_openapi_lists_project_score_route(client: TestClient) -> None:
    """Le schéma OpenAPI référence la route de scoring projet."""
    schema = client.get("/openapi.json").json()

    assert "/projects/{project_id}/score" in schema["paths"]
