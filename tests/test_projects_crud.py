"""Tests des endpoints CRUD projet (US-1.4, US-4.3)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create(client: TestClient, nom: str = "Projet A", direction: str = "Numérique") -> int:
    """Crée un projet et retourne son identifiant."""
    response = client.post(
        "/projects",
        json={
            "nom": nom,
            "description": "Description suffisamment longue pour valider.",
            "direction": direction,
            "duree_estimee_mois": 12,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_read_project_existant_retourne_200(client: TestClient) -> None:
    project_id = _create(client)
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["nom"] == "Projet A"


def test_read_project_inexistant_retourne_404(client: TestClient) -> None:
    response = client.get("/projects/99999")
    assert response.status_code == 404


def test_update_project_modifie_les_champs_fournis(client: TestClient) -> None:
    project_id = _create(client)
    response = client.put(
        f"/projects/{project_id}",
        json={"nom": "Projet renommé", "duree_estimee_mois": 24},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nom"] == "Projet renommé"
    assert body["duree_estimee_mois"] == 24
    assert body["direction"] == "Numérique"


def test_update_project_inexistant_retourne_404(client: TestClient) -> None:
    response = client.put("/projects/99999", json={"nom": "X"})
    assert response.status_code == 404


def test_list_projects_vide_retourne_liste_vide(client: TestClient) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_list_projects_trie_par_score_decroissant(client: TestClient) -> None:
    faible = _create(client, nom="Faible")
    fort = _create(client, nom="Fort")
    client.put(
        f"/projects/{faible}/dimensions",
        json={
            "rentabilite": 1,
            "alignement": 1,
            "risque": 1,
            "impact_operationnel": 1,
            "impact_social": 1,
            "faisabilite": 1,
        },
    )
    client.put(
        f"/projects/{fort}/dimensions",
        json={
            "rentabilite": 10,
            "alignement": 10,
            "risque": 10,
            "impact_operationnel": 10,
            "impact_social": 10,
            "faisabilite": 10,
        },
    )
    response = client.get("/projects")
    assert response.status_code == 200
    noms = [p["nom"] for p in response.json()]
    assert noms.index("Fort") < noms.index("Faible")


def test_list_projects_filtre_par_direction(client: TestClient) -> None:
    _create(client, nom="Num", direction="Numérique")
    _create(client, nom="Geo", direction="Geopost")
    response = client.get("/projects", params={"direction": "Geopost"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["nom"] == "Geo"
