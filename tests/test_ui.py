"""Tests de la mise à disposition de l'interface web statique."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_index_sert_la_page_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "BizPlan-IA" in response.text


def test_index_estampille_les_assets_avec_une_version(client: TestClient) -> None:
    """Les assets statiques portent une empreinte de version (cache-busting, BIZ-104)."""
    response = client.get("/")
    assert response.status_code == 200
    assert "__ASSET_VERSION__" not in response.text
    assert "/static/app.js?v=" in response.text
    assert "/static/style.css?v=" in response.text


def test_index_demande_la_revalidation_du_html(client: TestClient) -> None:
    """Le HTML est servi en no-cache pour récupérer les assets à jour (BIZ-104)."""
    response = client.get("/")
    assert response.status_code == 200
    assert "no-cache" in response.headers.get("cache-control", "")


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


def test_generation_affiche_un_indicateur_de_progression(client: TestClient) -> None:
    """La génération du business plan déclenche un overlay animé (BIZ-101)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "function runGeneration" in response.text
    assert "gen-progress" in response.text
    # Indicateur accessible et étapes décrites pour rassurer l'utilisateur.
    assert 'role="status"' in response.text
    assert "GENERATION_STEPS" in response.text


def test_generation_desactive_le_bouton_pendant_le_traitement(
    client: TestClient,
) -> None:
    """Le bouton de génération est désactivé pendant l'appel pour éviter les
    doubles soumissions (BIZ-101)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "button.disabled = true" in response.text
    assert 'dataset.busy === "1"' in response.text


def test_etape3_masque_les_notes_avant_analyse_ia(client: TestClient) -> None:
    """À l'étape 3, les notes restent masquées tant que l'IA n'a pas répondu (BIZ-107)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    # Les notes sont regroupées dans un conteneur masqué par défaut...
    assert '<div id="notes-wrap" hidden>' in response.text
    # ...et révélé uniquement lorsque l'IA répond ou en repli manuel.
    assert "if (notes) notes.hidden = false;" in response.text
    # Le calcul du score reste impossible tant que les notes ne sont pas affichées.
    assert 'id="next" disabled' in response.text


def test_etape3_justification_conditionnee_aux_modifications(
    client: TestClient,
) -> None:
    """Le champ de justification n'apparaît qu'en cas de modification d'une note (BIZ-107)."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert 'id="justif-wrap" hidden=""' in response.text
    assert "wrap.hidden = !isModified();" in response.text
