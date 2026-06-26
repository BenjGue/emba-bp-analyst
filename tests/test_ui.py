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


def test_dashboard_expose_le_telechargement_pdf(client: TestClient) -> None:
    """Le tableau de bord propose un lien d'export PDF par projet (BIZ-97)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "row-pdf" in response.text
    assert "/export?format=pdf" in response.text


def test_dashboard_pdf_conditionne_au_business_plan(client: TestClient) -> None:
    """Le bouton PDF du tableau de bord n'apparaît que si un BP existe (BIZ-97)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "p.has_business_plan" in response.text


def test_accueil_presente_le_projet_et_les_acces(client: TestClient) -> None:
    """La page d'accueil explique le projet et propose les deux accès (BIZ-98)."""
    response = client.get("/")
    assert response.status_code == 200
    # Modèle de la page d'accueil et accès explicites.
    assert 'id="tpl-home"' in response.text
    assert 'data-nav="home"' in response.text
    assert 'data-nav="dashboard"' in response.text
    assert 'data-nav="wizard"' in response.text


def test_accueil_est_la_vue_initiale(client: TestClient) -> None:
    """Au chargement, l'application affiche l'accueil et non le tableau de bord (BIZ-98)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "function renderHome" in response.text
    # La toute dernière vue invoquée au démarrage doit être l'accueil.
    assert response.text.rstrip().endswith("renderHome();")


def test_accueil_affiche_des_indicateurs(client: TestClient) -> None:
    """La page d'accueil agrège des indicateurs du portefeuille (BIZ-98)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "home-stats" in response.text
    assert "Score moyen" in response.text
