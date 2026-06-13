"""Tests des hypothèses financières (US-1.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

_VALID = {
    "investissement_initial": 100000,
    "revenus_annuels": 80000,
    "couts_annuels": 30000,
    "delai_rentabilite_mois": 36,
}


def test_upsert_financials_cree_les_hypotheses(client: TestClient, project_id: int) -> None:
    response = client.put(f"/projects/{project_id}/financials", json=_VALID)
    assert response.status_code == 200
    body = response.json()
    assert body["investissement_initial"] == 100000
    assert body["project_id"] == project_id


def test_upsert_financials_met_a_jour_les_hypotheses(client: TestClient, project_id: int) -> None:
    client.put(f"/projects/{project_id}/financials", json=_VALID)
    updated = {**_VALID, "revenus_annuels": 120000}
    response = client.put(f"/projects/{project_id}/financials", json=updated)
    assert response.status_code == 200
    assert response.json()["revenus_annuels"] == 120000

    second = client.get(f"/projects/{project_id}/financials")
    assert second.json()["revenus_annuels"] == 120000


def test_read_financials_absent_retourne_404(client: TestClient, project_id: int) -> None:
    response = client.get(f"/projects/{project_id}/financials")
    assert response.status_code == 404


def test_upsert_financials_projet_inexistant_retourne_404(
    client: TestClient,
) -> None:
    response = client.put("/projects/99999/financials", json=_VALID)
    assert response.status_code == 404


def test_upsert_financials_valeurs_negatives_retourne_422(
    client: TestClient, project_id: int
) -> None:
    invalid = {**_VALID, "investissement_initial": -10}
    response = client.put(f"/projects/{project_id}/financials", json=invalid)
    assert response.status_code == 422


def test_upsert_financials_delai_nul_retourne_422(client: TestClient, project_id: int) -> None:
    invalid = {**_VALID, "delai_rentabilite_mois": 0}
    response = client.put(f"/projects/{project_id}/financials", json=invalid)
    assert response.status_code == 422
