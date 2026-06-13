"""Tests de la mise à disposition de l'interface web statique."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_index_sert_la_page_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "BizPlan-IA" in response.text


def test_static_sert_la_feuille_de_style(client: TestClient) -> None:
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_static_sert_le_script(client: TestClient) -> None:
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "renderDashboard" in response.text
