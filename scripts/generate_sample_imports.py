"""Génère des classeurs Excel d'exemple pour tester l'import financier.

Les fichiers produits suivent le format décrit dans docs/Projet2.docx :

* format **détaillé** (BIZ-32) : le temps en lignes (mois ou années) et les
  catégories en colonnes — dépenses, recettes et agrégats. À téléverser via
  l'import « Importer un fichier Excel » → tableau détaillé
  (endpoint POST /projects/{id}/financials/import-detailed).
* format **simple** (BIZ-36) : un poste par ligne (libellé puis valeur).
  À téléverser via l'import simple
  (endpoint POST /projects/{id}/financials/import).

Usage :
    .venv\\Scripts\\python.exe scripts/generate_sample_imports.py

Les fichiers sont écrits dans samples/import-excel/.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "samples" / "import-excel"

# Projet d'exemple : « Assistant interne de tri prédictif » (intrapreneuriat
# La Poste). Données mensuelles sur 12 mois, cohérentes entre elles.
MONTHS = list(range(1, 13))

# Dépenses mensuelles (€).
SALAIRES = [18000] * 12
ACHAT_MATERIEL = [8000] + [0] * 11
ACHAT_LOGICIEL = [4000] + [500] * 11
CHARGES_FISCALES = [7000] * 12
FRAIS_ADMIN = [1200] * 12
FRAIS_BANCAIRES = [150] * 12
ACHATS_DIVERS = [600] * 12
AUTRES_DEPENSES = [400] * 12


def _col_sum(*series: list[int]) -> list[int]:
    """Somme terme à terme plusieurs séries de même longueur."""
    return [int(sum(values)) for values in zip(*series, strict=True)]


TOTAL_DEPENSES = _col_sum(
    SALAIRES,
    ACHAT_MATERIEL,
    ACHAT_LOGICIEL,
    CHARGES_FISCALES,
    FRAIS_ADMIN,
    FRAIS_BANCAIRES,
    ACHATS_DIVERS,
    AUTRES_DEPENSES,
)

# Recettes mensuelles (€) : montée en charge progressive.
CHIFFRE_AFFAIRES = [0, 0, 5000, 12000, 20000, 28000, 35000, 40000, 45000, 50000, 55000, 60000]
NOMBRE_CLIENTS = [0, 0, 2, 5, 9, 14, 18, 22, 26, 30, 34, 38]

# Répartition du CA par produit/service (40 / 30 / 20 / 10 %).
RECETTE_P1 = [round(ca * 0.40) for ca in CHIFFRE_AFFAIRES]
RECETTE_P2 = [round(ca * 0.30) for ca in CHIFFRE_AFFAIRES]
RECETTE_P3 = [round(ca * 0.20) for ca in CHIFFRE_AFFAIRES]
RECETTE_P4 = [ca - p1 - p2 - p3 for ca, p1, p2, p3 in zip(CHIFFRE_AFFAIRES, RECETTE_P1, RECETTE_P2, RECETTE_P3, strict=True)]

# Agrégats mensuels (illustratifs, dérivés du CA et des dépenses).
MARGE_BRUTE = [round(ca * 0.65) for ca in CHIFFRE_AFFAIRES]
EBE = [ca - dep for ca, dep in zip(CHIFFRE_AFFAIRES, TOTAL_DEPENSES, strict=True)]
RESULTAT_EXPLOITATION = [ebe - 1500 for ebe in EBE]
EBITDA = [ebe + 2000 for ebe in EBE]

# En-têtes de colonnes (libellés conformes à docs/Projet2.docx).
DETAILED_HEADER = [
    "Mois",
    "Salaires",
    "Achat matériel",
    "Achat logiciel",
    "Charges fiscales",
    "Frais administratifs",
    "Frais bancaires",
    "Achats divers",
    "Autres dépenses",
    "Total dépenses",
    "Nombre de clients",
    "Recette produit ou service 1",
    "Recette produit ou service 2",
    "Recette produit ou service 3",
    "Recette produit ou service 4",
    "Chiffre d'affaires",
    "Marge commerciale brute",
    "EBE",
    "Résultat d'exploitation",
    "EBITDA",
]


def _detailed_rows_monthly() -> list[list[object]]:
    """Construit les lignes du tableau détaillé mensuel (12 mois)."""
    rows: list[list[object]] = [DETAILED_HEADER]
    for i, month in enumerate(MONTHS):
        rows.append(
            [
                f"Mois {month}",
                SALAIRES[i],
                ACHAT_MATERIEL[i],
                ACHAT_LOGICIEL[i],
                CHARGES_FISCALES[i],
                FRAIS_ADMIN[i],
                FRAIS_BANCAIRES[i],
                ACHATS_DIVERS[i],
                AUTRES_DEPENSES[i],
                TOTAL_DEPENSES[i],
                NOMBRE_CLIENTS[i],
                RECETTE_P1[i],
                RECETTE_P2[i],
                RECETTE_P3[i],
                RECETTE_P4[i],
                CHIFFRE_AFFAIRES[i],
                MARGE_BRUTE[i],
                EBE[i],
                RESULTAT_EXPLOITATION[i],
                EBITDA[i],
            ]
        )
    return rows


def _detailed_rows_yearly() -> list[list[object]]:
    """Construit les lignes du tableau détaillé annuel (3 ans)."""
    header = ["Année", *DETAILED_HEADER[1:]]
    annees = [
        # Année 1 : agrégats annuels du tableau mensuel ci-dessus.
        {
            "Salaires": sum(SALAIRES),
            "Achat matériel": sum(ACHAT_MATERIEL),
            "Achat logiciel": sum(ACHAT_LOGICIEL),
            "Charges fiscales": sum(CHARGES_FISCALES),
            "Frais administratifs": sum(FRAIS_ADMIN),
            "Frais bancaires": sum(FRAIS_BANCAIRES),
            "Achats divers": sum(ACHATS_DIVERS),
            "Autres dépenses": sum(AUTRES_DEPENSES),
            "Total dépenses": sum(TOTAL_DEPENSES),
            "Nombre de clients": 38,
            "Chiffre d'affaires": sum(CHIFFRE_AFFAIRES),
        },
        # Année 2 : croissance.
        {
            "Salaires": 240000,
            "Achat matériel": 5000,
            "Achat logiciel": 9000,
            "Charges fiscales": 90000,
            "Frais administratifs": 16000,
            "Frais bancaires": 2200,
            "Achats divers": 8000,
            "Autres dépenses": 6000,
            "Total dépenses": 376200,
            "Nombre de clients": 110,
            "Chiffre d'affaires": 520000,
        },
        # Année 3 : maturité.
        {
            "Salaires": 300000,
            "Achat matériel": 6000,
            "Achat logiciel": 11000,
            "Charges fiscales": 112000,
            "Frais administratifs": 20000,
            "Frais bancaires": 2600,
            "Achats divers": 10000,
            "Autres dépenses": 7000,
            "Total dépenses": 468600,
            "Nombre de clients": 240,
            "Chiffre d'affaires": 760000,
        },
    ]
    rows: list[list[object]] = [header]
    for index, an in enumerate(annees, start=1):
        ca = an["Chiffre d'affaires"]
        p1, p2, p3 = round(ca * 0.40), round(ca * 0.30), round(ca * 0.20)
        p4 = ca - p1 - p2 - p3
        ebe = ca - an["Total dépenses"]
        rows.append(
            [
                f"Année {index}",
                an["Salaires"],
                an["Achat matériel"],
                an["Achat logiciel"],
                an["Charges fiscales"],
                an["Frais administratifs"],
                an["Frais bancaires"],
                an["Achats divers"],
                an["Autres dépenses"],
                an["Total dépenses"],
                an["Nombre de clients"],
                p1,
                p2,
                p3,
                p4,
                ca,
                round(ca * 0.65),
                ebe,
                ebe - 18000,
                ebe + 24000,
            ]
        )
    return rows


def _simple_rows() -> list[list[object]]:
    """Construit les lignes du format simple (un poste par ligne)."""
    return [
        ["Poste", "Valeur"],
        ["Investissement initial", 113750],
        ["Revenus annuels", 350000],
        ["Coûts annuels", 345700],
        ["Délai de rentabilité (mois)", 12],
    ]


def _write(rows: list[list[object]], filename: str) -> Path:
    """Écrit les lignes dans un classeur Excel et retourne son chemin."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Business plan"
    for row in rows:
        sheet.append(row)
    path = OUTPUT_DIR / filename
    workbook.save(path)
    return path


def main() -> None:
    """Génère les trois classeurs d'exemple."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = [
        _write(_detailed_rows_monthly(), "bizplan-detaille-mensuel.xlsx"),
        _write(_detailed_rows_yearly(), "bizplan-detaille-annuel.xlsx"),
        _write(_simple_rows(), "bizplan-simple.xlsx"),
    ]
    for path in written:
        print(f"✅ {path.relative_to(OUTPUT_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
