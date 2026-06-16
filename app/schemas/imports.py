"""Schémas Pydantic de l'import Excel des données financières (BIZ-36).

Le porteur de projet téléverse un classeur Excel multi-colonnes ; le backend en
extrait les hypothèses financières (qui sont ensuite persistées comme une saisie
manuelle) et conserve une trace du fichier d'origine.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.financial import FinancialAssumptionResponse


class FinancialImportMetadata(BaseModel):
    """Métadonnées du fichier Excel importé et conservé.

    Attributes:
        filename: Nom du fichier d'origine.
        content_type: Type MIME déclaré à l'upload.
        size_bytes: Taille du fichier, en octets.
        uploaded_at: Horodatage de l'import (UTC).
    """

    model_config = ConfigDict(from_attributes=True)

    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime


class FinancialImportResult(BaseModel):
    """Résultat d'un import : hypothèses extraites + trace du fichier.

    Attributes:
        financials: Hypothèses financières extraites et persistées.
        import_file: Métadonnées du fichier Excel conservé.
    """

    financials: FinancialAssumptionResponse
    import_file: FinancialImportMetadata


class FinancialStatementData(BaseModel):
    """Tableau financier détaillé multi-colonnes (BIZ-32).

    Représente le format de la spécification : le temps en lignes et les
    catégories en colonnes (dépenses, recettes, agrégats). Chaque série est une
    liste de valeurs alignée sur ``periods``.

    Attributes:
        period_unit: Granularité temporelle détectée (``semaine``/``mois``/``annee``).
        periods: Libellés des périodes, dans l'ordre.
        depenses: Séries de dépenses par poste canonique.
        recettes: Séries de recettes par poste canonique.
        agregats: Séries d'agrégats par poste canonique.
    """

    model_config = ConfigDict(from_attributes=True)

    period_unit: str
    periods: list[str]
    depenses: dict[str, list[float]]
    recettes: dict[str, list[float]]
    agregats: dict[str, list[float]]


class FinancialStatementResult(BaseModel):
    """Résultat d'un import détaillé : tableau + hypothèses dérivées + fichier.

    Attributes:
        statement: Tableau financier détaillé conservé.
        financials: Hypothèses financières dérivées et persistées.
        import_file: Métadonnées du fichier Excel conservé.
    """

    statement: FinancialStatementData
    financials: FinancialAssumptionResponse
    import_file: FinancialImportMetadata
