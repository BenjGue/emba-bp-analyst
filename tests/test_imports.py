"""Tests de l'import Excel des données financières (BIZ-36)."""

from __future__ import annotations

import io

import openpyxl
from fastapi.testclient import TestClient

_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx(rows: list[list[object]]) -> bytes:
    """Construit un classeur Excel en mémoire à partir de lignes.

    Args:
        rows: Lignes (libellé puis valeurs) à écrire dans la feuille active.

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


def _valid_rows() -> list[list[object]]:
    """Retourne un classeur valide simple (une valeur par poste)."""
    return [
        ["Poste", "Valeur"],
        ["Investissement initial", 100000],
        ["Revenus annuels", 80000],
        ["Coûts annuels", 30000],
        ["Délai de rentabilité (mois)", 36],
    ]


def _upload(client: TestClient, project_id: int, content: bytes, name: str = "data.xlsx"):
    """Téléverse un fichier sur l'endpoint d'import."""
    return client.post(
        f"/projects/{project_id}/financials/import",
        files={"file": (name, content, _CONTENT_TYPE)},
    )


def test_import_xlsx_valide_extrait_les_finances(client: TestClient, project_id: int) -> None:
    response = _upload(client, project_id, _xlsx(_valid_rows()))
    assert response.status_code == 201
    body = response.json()
    assert body["financials"]["investissement_initial"] == 100000
    assert body["financials"]["revenus_annuels"] == 80000
    assert body["financials"]["couts_annuels"] == 30000
    assert body["financials"]["delai_rentabilite_mois"] == 36
    assert body["import_file"]["filename"] == "data.xlsx"
    assert body["import_file"]["size_bytes"] > 0


def test_import_persiste_les_hypotheses(client: TestClient, project_id: int) -> None:
    _upload(client, project_id, _xlsx(_valid_rows()))
    response = client.get(f"/projects/{project_id}/financials")
    assert response.status_code == 200
    assert response.json()["revenus_annuels"] == 80000


def test_import_multi_colonnes_moyenne_les_annees(client: TestClient, project_id: int) -> None:
    rows = [
        ["Poste", "Année 1", "Année 2", "Année 3"],
        ["Investissement initial", 90000],
        ["Revenus annuels", 60000, 80000, 100000],
        ["Coûts annuels", 20000, 30000, 40000],
        ["Délai de rentabilité", 24],
    ]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 201
    body = response.json()
    assert body["financials"]["revenus_annuels"] == 80000
    assert body["financials"]["couts_annuels"] == 30000


def test_import_extension_invalide_retourne_422(client: TestClient, project_id: int) -> None:
    response = client.post(
        f"/projects/{project_id}/financials/import",
        files={"file": ("data.csv", b"a,b,c", "text/csv")},
    )
    assert response.status_code == 422


def test_import_donnees_manquantes_retourne_422(client: TestClient, project_id: int) -> None:
    rows = [["Poste", "Valeur"], ["Revenus annuels", 80000]]
    response = _upload(client, project_id, _xlsx(rows))
    assert response.status_code == 422
    assert "manquantes" in response.json()["detail"]


def test_import_fichier_corrompu_retourne_422(client: TestClient, project_id: int) -> None:
    response = _upload(client, project_id, b"ceci n'est pas un xlsx")
    assert response.status_code == 422


def test_import_projet_inexistant_retourne_404(client: TestClient) -> None:
    response = _upload(client, 99999, _xlsx(_valid_rows()))
    assert response.status_code == 404


def test_import_fichier_trop_volumineux_retourne_413(client: TestClient, project_id: int) -> None:
    big = _xlsx(_valid_rows()) + b"\x00" * (2 * 1024 * 1024 + 1)
    response = _upload(client, project_id, big)
    assert response.status_code == 413


def test_metadata_apres_import_retourne_200(client: TestClient, project_id: int) -> None:
    _upload(client, project_id, _xlsx(_valid_rows()))
    response = client.get(f"/projects/{project_id}/financials/import")
    assert response.status_code == 200
    assert response.json()["filename"] == "data.xlsx"


def test_metadata_sans_import_retourne_404(client: TestClient, project_id: int) -> None:
    response = client.get(f"/projects/{project_id}/financials/import")
    assert response.status_code == 404


def test_telechargement_du_fichier_importe(client: TestClient, project_id: int) -> None:
    content = _xlsx(_valid_rows())
    _upload(client, project_id, content)
    response = client.get(f"/projects/{project_id}/financials/import/file")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert response.content == content


def test_reimport_remplace_le_fichier_precedent(client: TestClient, project_id: int) -> None:
    _upload(client, project_id, _xlsx(_valid_rows()), name="premier.xlsx")
    rows = [
        ["Poste", "Valeur"],
        ["Investissement initial", 50000],
        ["Revenus annuels", 70000],
        ["Coûts annuels", 25000],
        ["Délai de rentabilité", 18],
    ]
    _upload(client, project_id, _xlsx(rows), name="second.xlsx")
    meta = client.get(f"/projects/{project_id}/financials/import").json()
    assert meta["filename"] == "second.xlsx"
    fin = client.get(f"/projects/{project_id}/financials").json()
    assert fin["revenus_annuels"] == 70000
