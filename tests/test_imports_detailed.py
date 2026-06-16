"""Tests de l'import Excel détaillé multi-colonnes (BIZ-32).

Format : le temps en lignes (semaines/mois/années), les catégories en colonnes
(dépenses, recettes, agrégats). Les hypothèses financières scalaires sont
dérivées de façon déterministe du tableau.
"""

from __future__ import annotations

import io

import openpyxl
from fastapi.testclient import TestClient

from app.services.imports import ParsedStatement, derive_assumptions

_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx(rows: list[list[object]]) -> bytes:
    """Construit un classeur Excel en mémoire à partir de lignes.

    Args:
        rows: Lignes à écrire dans la feuille active (en-tête puis périodes).

    Returns:
        Le contenu binaire du fichier .xlsx.
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _upload(client: TestClient, project_id: int, content: bytes, name: str = "detail.xlsx"):
    """Téléverse un fichier sur l'endpoint d'import détaillé."""
    return client.post(
        f"/projects/{project_id}/financials/import-detailed",
        files={"file": (name, content, _CONTENT_TYPE)},
    )


def _simple_rows() -> list[list[object]]:
    """Classeur valide : 3 mois, chiffre d'affaires et total dépenses."""
    return [
        ["Mois", "Chiffre d'affaires", "Total dépenses"],
        ["M1", 1000, 2000],
        ["M2", 2000, 1500],
        ["M3", 3000, 1000],
    ]


def test_import_detaille_valide_retourne_201_et_tableau(
    client: TestClient, project_id: int
) -> None:
    response = _upload(client, project_id, _xlsx(_simple_rows()))
    assert response.status_code == 201
    body = response.json()
    statement = body["statement"]
    assert statement["period_unit"] == "mois"
    assert statement["periods"] == ["M1", "M2", "M3"]
    assert statement["recettes"]["chiffre_affaires"] == [1000, 2000, 3000]
    assert statement["depenses"]["total_depenses"] == [2000, 1500, 1000]
    assert body["import_file"]["filename"] == "detail.xlsx"


def test_import_detaille_derive_les_hypotheses(client: TestClient, project_id: int) -> None:
    response = _upload(client, project_id, _xlsx(_simple_rows()))
    f = response.json()["financials"]
    # total CA = 6000 sur 3 mois -> annualisé x4 = 24000 ; total dépenses 4500 -> 18000.
    assert f["revenus_annuels"] == 24000
    assert f["couts_annuels"] == 18000
    # creux de trésorerie cumulée = -1000 ; rentabilité au 3e mois.
    assert f["investissement_initial"] == 1000
    assert f["delai_rentabilite_mois"] == 3


def test_import_detaille_persiste_les_hypotheses(client: TestClient, project_id: int) -> None:
    _upload(client, project_id, _xlsx(_simple_rows()))
    response = client.get(f"/projects/{project_id}/financials")
    assert response.status_code == 200
    assert response.json()["revenus_annuels"] == 24000


def test_statement_consultable_apres_import(client: TestClient, project_id: int) -> None:
    _upload(client, project_id, _xlsx(_simple_rows()))
    response = client.get(f"/projects/{project_id}/financials/statement")
    assert response.status_code == 200
    assert response.json()["periods"] == ["M1", "M2", "M3"]


def test_statement_absent_retourne_404(client: TestClient, project_id: int) -> None:
    response = client.get(f"/projects/{project_id}/financials/statement")
    assert response.status_code == 404


def test_import_detaille_reconnait_postes_detailles(client: TestClient, project_id: int) -> None:
    rows = [
        [
            "Mois",
            "Salaires",
            "Achat matériel",
            "Recette produit ou service 1",
            "Chiffre d'affaires",
        ],
        ["M1", 800, 200, 500, 1500],
        ["M2", 800, 0, 700, 1800],
    ]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 201
    statement = response.json()["statement"]
    assert statement["depenses"]["salaires"] == [800, 800]
    assert statement["depenses"]["achat_materiel"] == [200, 0]
    assert statement["recettes"]["recette_produit_1"] == [500, 700]
    assert statement["recettes"]["chiffre_affaires"] == [1500, 1800]


def test_import_detaille_granularite_annee(client: TestClient, project_id: int) -> None:
    rows = [
        ["Année", "Chiffre d'affaires", "Total dépenses"],
        ["2024", 1000, 400],
        ["2025", 1000, 400],
    ]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 201
    body = response.json()
    assert body["statement"]["period_unit"] == "annee"
    # total CA 2000 sur 24 mois -> annualisé x0.5 = 1000.
    assert body["financials"]["revenus_annuels"] == 1000


def test_import_detaille_recettes_manquantes_retourne_422(
    client: TestClient, project_id: int
) -> None:
    rows = [["Mois", "Total dépenses"], ["M1", 1000]]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 422
    assert "recettes" in response.json()["detail"].lower()


def test_import_detaille_depenses_manquantes_retourne_422(
    client: TestClient, project_id: int
) -> None:
    rows = [["Mois", "Chiffre d'affaires"], ["M1", 1000]]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 422
    assert "dépenses" in response.json()["detail"].lower()


def test_import_detaille_colonnes_non_reconnues_retourne_422(
    client: TestClient, project_id: int
) -> None:
    rows = [["Mois", "Colonne X", "Colonne Y"], ["M1", 1, 2]]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 422


def test_import_detaille_projet_inexistant_retourne_404(client: TestClient) -> None:
    response = _upload(client, 99999, _xlsx(_simple_rows()))
    assert response.status_code == 404


def test_derive_assumptions_jamais_rentable_plafonne_delai() -> None:
    statement = ParsedStatement(
        period_unit="mois",
        periods=["M1", "M2"],
        depenses={"total_depenses": [1000.0, 1000.0]},
        recettes={"chiffre_affaires": [100.0, 100.0]},
        agregats={},
    )
    derived = derive_assumptions(statement)
    assert derived.delai_rentabilite_mois == 600
    assert derived.investissement_initial == 1800.0
