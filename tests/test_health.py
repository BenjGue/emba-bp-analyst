"""Tests du healthcheck (``GET /health``)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import __version__


def test_health_returns_200_ok(client: TestClient) -> None:
    """Le healthcheck répond 200 avec un statut ``ok``."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_exposes_app_name_and_version(client: TestClient) -> None:
    """Le healthcheck expose le nom de l'application et la version courante."""
    response = client.get("/health")

    body = response.json()
    assert body["app_name"] == "BizPlan-IA"
    assert body["version"] == __version__


def test_openapi_docs_available(client: TestClient) -> None:
    """La documentation OpenAPI auto-générée est servie sur ``/docs``."""
    response = client.get("/docs")

    assert response.status_code == 200


def test_openapi_schema_lists_health_route(client: TestClient) -> None:
    """Le schéma OpenAPI référence bien la route ``/health``."""
    schema = client.get("/openapi.json").json()

    assert "/health" in schema["paths"]
