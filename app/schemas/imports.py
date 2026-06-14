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
