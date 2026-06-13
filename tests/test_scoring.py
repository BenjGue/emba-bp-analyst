"""Tests du moteur de score de pertinence (US-2.1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.schemas.score import StrategicDimensions
from app.services.scoring import WEIGHTS, compute_score

_ALL_ZERO = {
    "rentabilite": 0,
    "alignement": 0,
    "risque": 0,
    "impact_operationnel": 0,
    "impact_social": 0,
    "faisabilite": 0,
}
_ALL_TEN = dict.fromkeys(_ALL_ZERO, 10)


def test_weights_sum_to_one() -> None:
    """La somme des pondérations vaut exactement 1.0."""
    assert pytest.approx(sum(WEIGHTS.values())) == 1.0


def test_compute_score_all_zero_returns_zero() -> None:
    """Toutes les notes à 0 donnent un score global de 0."""
    result = compute_score(StrategicDimensions(**_ALL_ZERO))

    assert result.total == 0.0
    assert all(detail.contribution == 0.0 for detail in result.dimensions.values())


def test_compute_score_all_ten_returns_hundred() -> None:
    """Toutes les notes à 10 donnent un score global de 100."""
    result = compute_score(StrategicDimensions(**_ALL_TEN))

    assert result.total == 100.0


def test_compute_score_mixed_is_deterministic_value() -> None:
    """Un jeu de notes mixtes produit la contribution pondérée attendue."""
    dimensions = StrategicDimensions(
        rentabilite=8,
        alignement=6,
        risque=5,
        impact_operationnel=7,
        impact_social=4,
        faisabilite=9,
    )

    result = compute_score(dimensions)

    # 8*0.3 + 6*0.2 + 5*0.2 + 7*0.1 + 4*0.1 + 9*0.1 = 6.6 (sur 10) -> 66.0 / 100
    assert result.total == 66.0
    assert result.dimensions["rentabilite"].contribution == 24.0
    assert result.dimensions["rentabilite"].poids == 0.30


def test_compute_score_is_deterministic() -> None:
    """Mêmes entrées → même sortie (calcul déterministe)."""
    dimensions = StrategicDimensions(
        rentabilite=3,
        alignement=7,
        risque=2,
        impact_operationnel=8,
        impact_social=5,
        faisabilite=6,
    )

    assert compute_score(dimensions) == compute_score(dimensions)


def test_compute_score_lists_all_six_dimensions() -> None:
    """Le détail retourné couvre les 6 dimensions stratégiques."""
    result = compute_score(StrategicDimensions(**_ALL_TEN))

    assert set(result.dimensions) == set(WEIGHTS)


def test_score_endpoint_returns_200_and_total(client: TestClient) -> None:
    """POST /score renvoie 200 avec le score global et le détail."""
    response = client.post("/score", json=_ALL_TEN)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 100.0
    assert set(body["dimensions"]) == set(WEIGHTS)


def test_score_endpoint_rejects_out_of_range_note(client: TestClient) -> None:
    """Une note hors de [0, 10] renvoie une erreur de validation 422."""
    payload = {**_ALL_TEN, "rentabilite": 11}

    response = client.post("/score", json=payload)

    assert response.status_code == 422


def test_score_endpoint_rejects_missing_dimension(client: TestClient) -> None:
    """Une dimension manquante renvoie une erreur de validation 422."""
    payload = {k: v for k, v in _ALL_TEN.items() if k != "faisabilite"}

    response = client.post("/score", json=payload)

    assert response.status_code == 422
