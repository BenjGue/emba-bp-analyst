"""Tests de la génération et de l'export du business plan (US-4.1, US-4.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

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


def _prepare(client: TestClient, project_id: int) -> None:
    """Saisit les hypothèses financières et l'évaluation stratégique."""
    client.put(f"/projects/{project_id}/financials", json=_FINANCIALS)
    client.put(f"/projects/{project_id}/dimensions", json=_DIMS)


def test_generate_sans_financials_retourne_400(client: TestClient, project_id: int) -> None:
    response = client.post(f"/projects/{project_id}/generate")
    assert response.status_code == 400


def test_generate_produit_un_business_plan(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    response = client.post(f"/projects/{project_id}/generate")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "generated"
    assert body["sections"]
    assert len(body["scenarios"]) == 3


def test_generate_inclut_la_section_analyse_concurrentielle(
    client: TestClient, project_id: int
) -> None:
    """Le business plan expose une section concurrentielle distincte (BIZ-90)."""
    _prepare(client, project_id)
    response = client.post(f"/projects/{project_id}/generate")
    assert response.status_code == 201
    assert "Analyse concurrentielle" in response.json()["sections"]


def test_generate_est_idempotent(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    client.post(f"/projects/{project_id}/generate")
    response = client.post(f"/projects/{project_id}/generate")
    assert response.status_code == 201
    assert len(response.json()["scenarios"]) == 3


def test_generate_projet_inexistant_retourne_404(client: TestClient) -> None:
    response = client.post("/projects/99999/generate")
    assert response.status_code == 404


def test_read_bp_sans_generation_retourne_404(client: TestClient, project_id: int) -> None:
    response = client.get(f"/projects/{project_id}/bp")
    assert response.status_code == 404


def test_read_bp_apres_generation_retourne_200(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    client.post(f"/projects/{project_id}/generate")
    response = client.get(f"/projects/{project_id}/bp")
    assert response.status_code == 200
    assert response.json()["sections"]


def test_export_markdown_retourne_un_fichier(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    client.post(f"/projects/{project_id}/generate")
    response = client.get(f"/projects/{project_id}/export", params={"format": "md"})
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert response.text.startswith("# Business Plan")


def test_export_pdf_retourne_un_fichier(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    client.post(f"/projects/{project_id}/generate")
    response = client.get(f"/projects/{project_id}/export", params={"format": "pdf"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_export_format_invalide_retourne_422(client: TestClient, project_id: int) -> None:
    _prepare(client, project_id)
    client.post(f"/projects/{project_id}/generate")
    response = client.get(f"/projects/{project_id}/export", params={"format": "xml"})
    assert response.status_code == 422


def test_export_sans_business_plan_retourne_404(client: TestClient, project_id: int) -> None:
    response = client.get(f"/projects/{project_id}/export", params={"format": "md"})
    assert response.status_code == 404
