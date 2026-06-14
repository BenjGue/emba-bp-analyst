"""Tests de la rédaction de description assistée par IA (BIZ-37)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import FakeAiClient


def _install_fake(client: TestClient, text: str) -> FakeAiClient:
    """Installe un faux client IA via l'override de dépendance FastAPI."""
    from app.services.ai.deps import get_ai_dependency

    fake = FakeAiClient(lambda system, user: text)
    client.app.dependency_overrides[get_ai_dependency] = lambda: fake
    return fake


def test_draft_description_retourne_le_texte_genere(client: TestClient) -> None:
    fake = _install_fake(client, "Une description claire et structurée du projet.")
    response = client.post(
        "/projects/draft-description",
        json={"idees": "plateforme de suivi colis", "direction": "Numérique"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Une description claire et structurée du projet."
    assert len(fake.calls) == 1


def test_draft_description_borne_a_1000_caracteres(client: TestClient) -> None:
    _install_fake(client, "x" * 1500)
    response = client.post(
        "/projects/draft-description",
        json={"idees": "idée longue", "direction": "Geopost"},
    )
    assert response.status_code == 200
    assert len(response.json()["description"]) == 1000


def test_draft_description_ia_desactivee_retourne_503(client: TestClient) -> None:
    response = client.post(
        "/projects/draft-description",
        json={"idees": "idée", "direction": "Numérique"},
    )
    assert response.status_code == 503


def test_draft_description_idees_vides_retourne_422(client: TestClient) -> None:
    _install_fake(client, "texte")
    response = client.post(
        "/projects/draft-description",
        json={"idees": "", "direction": "Numérique"},
    )
    assert response.status_code == 422
