"""Tests de l'endpoint de création de projet (US-1.1)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _valid_payload() -> dict[str, object]:
    """Retourne un corps de requête valide pour créer un projet."""
    return {
        "nom": "Casier connecté",
        "description": "Casier de retrait de colis connecté en bureau de poste.",
        "direction": "Services-Courrier-Colis",
        "duree_estimee_mois": 18,
    }


def test_create_project_payload_valide_retourne_201(client: TestClient) -> None:
    """Un corps valide crée le projet et renvoie 201 avec son identifiant."""
    response = client.post("/projects", json=_valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["nom"] == "Casier connecté"
    assert body["direction"] == "Services-Courrier-Colis"
    assert body["duree_estimee_mois"] == 18
    assert "created_at" in body


def test_create_project_persiste_le_projet(client: TestClient) -> None:
    """Le projet créé est ensuite scorable (preuve de persistance en base)."""
    project_id = client.post("/projects", json=_valid_payload()).json()["id"]

    dimensions = {
        "rentabilite": 8,
        "alignement": 6,
        "risque": 5,
        "impact_operationnel": 7,
        "impact_social": 4,
        "faisabilite": 9,
    }
    score_response = client.post(f"/projects/{project_id}/score", json=dimensions)

    assert score_response.status_code == 200


def test_create_project_nom_manquant_retourne_422(client: TestClient) -> None:
    """Un nom absent déclenche une erreur de validation 422."""
    payload = _valid_payload()
    del payload["nom"]

    response = client.post("/projects", json=payload)

    assert response.status_code == 422


def test_create_project_nom_vide_retourne_422(client: TestClient) -> None:
    """Un nom vide (chaîne vide) déclenche une erreur de validation 422."""
    payload = _valid_payload()
    payload["nom"] = ""

    response = client.post("/projects", json=payload)

    assert response.status_code == 422


def test_create_project_direction_invalide_retourne_422(client: TestClient) -> None:
    """Une direction hors liste fixe déclenche une erreur de validation 422."""
    payload = _valid_payload()
    payload["direction"] = "Direction Inconnue"

    response = client.post("/projects", json=payload)

    assert response.status_code == 422


def test_create_project_duree_non_positive_retourne_422(client: TestClient) -> None:
    """Une durée estimée nulle ou négative déclenche une erreur 422."""
    payload = _valid_payload()
    payload["duree_estimee_mois"] = 0

    response = client.post("/projects", json=payload)

    assert response.status_code == 422


def test_create_project_nom_trop_long_retourne_422(client: TestClient) -> None:
    """Un nom dépassant 200 caractères déclenche une erreur 422."""
    payload = _valid_payload()
    payload["nom"] = "x" * 201

    response = client.post("/projects", json=payload)

    assert response.status_code == 422


def test_create_project_expose_dans_openapi(client: TestClient) -> None:
    """La route POST /projects est documentée dans le schéma OpenAPI."""
    schema = client.get("/openapi.json").json()

    assert "post" in schema["paths"]["/projects"]
