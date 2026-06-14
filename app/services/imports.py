"""Service d'import Excel des données financières (BIZ-36).

Parse un classeur Excel multi-colonnes, en extrait les hypothèses financières,
les persiste (comme une saisie manuelle) et conserve le fichier d'origine.

Principe : l'analyse est purement déterministe côté backend. Aucune donnée n'est
inventée ; si une valeur attendue est absente, l'import échoue avec un message
explicite plutôt que de produire une hypothèse erronée.
"""

from __future__ import annotations

import io
import unicodedata
from collections.abc import Iterable

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.models import FinancialImport
from app.schemas.financial import FinancialAssumptionCreate
from app.services.financials import save_financials
from app.services.projects import get_project

#: Taille maximale acceptée pour le fichier importé (2 Mio).
MAX_IMPORT_BYTES = 2 * 1024 * 1024

#: Extensions de fichier autorisées.
_ALLOWED_EXTENSIONS = (".xlsx", ".xlsm")

#: Types MIME autorisés (Excel moderne).
_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel.sheet.macroEnabled.12",
        "application/octet-stream",
        "",
    }
)


class ExcelImportError(Exception):
    """Levée lorsqu'un fichier Excel est invalide ou inexploitable."""


def _normalize(label: object) -> str:
    """Normalise un libellé : minuscules, sans accents ni espaces superflus.

    Args:
        label: Valeur de cellule à normaliser.

    Returns:
        Le libellé normalisé (chaîne vide si la cellule n'est pas textuelle).
    """
    if not isinstance(label, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", label)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.strip().lower()


def _numbers(cells: Iterable[object]) -> list[float]:
    """Extrait les valeurs numériques d'une suite de cellules.

    Args:
        cells: Cellules d'une ligne (hors libellé).

    Returns:
        La liste des nombres trouvés, dans l'ordre.
    """
    values: list[float] = []
    for cell in cells:
        if isinstance(cell, bool):
            continue
        if isinstance(cell, (int, float)):
            values.append(float(cell))
    return values


def _mean(values: list[float]) -> float:
    """Retourne la moyenne d'une liste de nombres (0.0 si vide)."""
    return sum(values) / len(values) if values else 0.0


def parse_financials_xlsx(content: bytes) -> FinancialAssumptionCreate:
    """Extrait les hypothèses financières d'un classeur Excel.

    Le format attendu est une feuille « libellé puis valeurs » : la première
    cellule de chaque ligne porte un libellé (ex. « Revenus annuels ») et les
    cellules suivantes contiennent une ou plusieurs valeurs annuelles. Pour les
    postes pluriannuels (revenus, coûts), la moyenne des colonnes est retenue.

    Args:
        content: Contenu binaire du fichier Excel.

    Returns:
        Les hypothèses financières extraites et validées.

    Raises:
        ExcelImportError: Si le fichier est illisible ou s'il manque une donnée.
    """
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # openpyxl lève divers types selon la corruption.
        raise ExcelImportError("Fichier Excel illisible ou corrompu.") from exc

    try:
        sheet = workbook.active
        if sheet is None:
            raise ExcelImportError("Le classeur ne contient aucune feuille.")

        investissement: float | None = None
        revenus: float | None = None
        couts: float | None = None
        delai: float | None = None

        for row in sheet.iter_rows(values_only=True):
            if not row:
                continue
            label = _normalize(row[0])
            if not label:
                continue
            nums = _numbers(row[1:])
            if not nums:
                continue
            if investissement is None and "investissement" in label:
                investissement = nums[0]
            elif revenus is None and "revenu" in label:
                revenus = _mean(nums)
            elif couts is None and ("cout" in label or "charge" in label):
                couts = _mean(nums)
            elif delai is None and ("delai" in label or "rentab" in label or "retour" in label):
                delai = nums[0]
    finally:
        workbook.close()

    missing = [
        name
        for name, value in (
            ("investissement initial", investissement),
            ("revenus annuels", revenus),
            ("coûts annuels", couts),
            ("délai de rentabilité", delai),
        )
        if value is None
    ]
    if missing:
        raise ExcelImportError(
            "Données financières manquantes dans le fichier : " + ", ".join(missing) + "."
        )

    try:
        return FinancialAssumptionCreate(
            investissement_initial=float(investissement),  # type: ignore[arg-type]
            revenus_annuels=round(float(revenus), 2),  # type: ignore[arg-type]
            couts_annuels=round(float(couts), 2),  # type: ignore[arg-type]
            delai_rentabilite_mois=int(round(float(delai))),  # type: ignore[arg-type]
        )
    except ValueError as exc:
        raise ExcelImportError("Valeurs financières invalides dans le fichier.") from exc


def _validate_upload(filename: str, content: bytes) -> None:
    """Valide l'extension et la taille du fichier téléversé.

    Args:
        filename: Nom du fichier d'origine.
        content: Contenu binaire.

    Raises:
        ExcelImportError: Si l'extension n'est pas autorisée ou le fichier vide.
        FileTooLargeError: Si le fichier dépasse la taille maximale.
    """
    name = filename.lower()
    if not name.endswith(_ALLOWED_EXTENSIONS):
        raise ExcelImportError(
            "Format non supporté : seuls les fichiers .xlsx/.xlsm sont acceptés."
        )
    if not content:
        raise ExcelImportError("Le fichier importé est vide.")
    if len(content) > MAX_IMPORT_BYTES:
        raise FileTooLargeError(len(content))


class FileTooLargeError(Exception):
    """Levée lorsqu'un fichier importé dépasse la taille maximale autorisée."""


def import_financials(
    db: Session,
    project_id: int,
    *,
    filename: str,
    content_type: str,
    content: bytes,
) -> tuple[FinancialImport, FinancialAssumptionCreate]:
    """Importe un fichier Excel : valide, parse, persiste et conserve le fichier.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet rattaché.
        filename: Nom du fichier d'origine.
        content_type: Type MIME déclaré à l'upload.
        content: Contenu binaire du fichier.

    Returns:
        Le couple ``(import persisté, hypothèses extraites)``.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
        ExcelImportError: Si le fichier est invalide ou inexploitable.
        FileTooLargeError: Si le fichier dépasse la taille maximale.
    """
    project = get_project(db, project_id)
    _validate_upload(filename, content)

    parsed = parse_financials_xlsx(content)
    save_financials(db, project_id, parsed)

    record = project.financial_import
    if record is None:
        record = FinancialImport(project_id=project_id)
        db.add(record)
    record.filename = filename[:255]
    record.content_type = (content_type or "application/octet-stream")[:100]
    record.size_bytes = len(content)
    record.content = content

    db.commit()
    db.refresh(record)
    return record, parsed


def get_import(db: Session, project_id: int) -> FinancialImport:
    """Retourne le dernier fichier Excel importé pour un projet.

    Args:
        db: Session de base de données.
        project_id: Identifiant du projet rattaché.

    Returns:
        Le fichier importé persisté.

    Raises:
        ProjectNotFoundError: Si le projet n'existe pas.
        ImportNotFoundError: Si aucun fichier n'a été importé.
    """
    project = get_project(db, project_id)
    if project.financial_import is None:
        raise ImportNotFoundError(project_id)
    return project.financial_import


class ImportNotFoundError(Exception):
    """Levée lorsqu'aucun fichier Excel n'a été importé pour le projet."""
