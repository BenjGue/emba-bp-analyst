"""Service d'export du business plan (US-4.2).

Produit le business plan au format Markdown et PDF, ainsi que la note de
synthèse CODIR en texte brut. Le nom de fichier suit la convention
``bizplan-{slug}-{date}``.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.models import BusinessPlan, Project


def slugify(value: str) -> str:
    """Normalise une chaîne en slug ASCII utilisable dans un nom de fichier.

    Args:
        value: Chaîne source.

    Returns:
        Un slug en minuscules, sans accent ni caractère spécial.
    """
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return ascii_value or "projet"


def export_filename(project: Project, extension: str) -> str:
    """Construit le nom de fichier d'export ``bizplan-{slug}-{date}.{ext}``.

    Args:
        project: Projet exporté.
        extension: Extension de fichier (``md`` ou ``pdf``).

    Returns:
        Le nom de fichier normalisé.
    """
    date = datetime.now(UTC).strftime("%Y%m%d")
    return f"bizplan-{slugify(project.nom)}-{date}.{extension}"


def to_markdown(project: Project, business_plan: BusinessPlan) -> str:
    """Rend le business plan complet au format Markdown.

    Args:
        project: Projet source.
        business_plan: Business plan généré.

    Returns:
        Le document Markdown (titre, sections, note de synthèse).
    """
    lines: list[str] = [
        f"# Business Plan — {project.nom}",
        "",
        f"**Direction :** {project.direction}  ",
        f"**Durée estimée :** {project.duree_estimee_mois} mois",
        "",
    ]
    for index, (title, content) in enumerate(business_plan.sections.items(), start=1):
        lines.append(f"## {index}. {title}")
        lines.append("")
        lines.append(content)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(business_plan.synthese_codir)
    lines.append("")
    return "\n".join(lines)


def to_pdf(project: Project, business_plan: BusinessPlan) -> bytes:
    """Rend le business plan complet au format PDF.

    Args:
        project: Projet source.
        business_plan: Business plan généré.

    Returns:
        Le contenu binaire du PDF.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.multi_cell(
        0,
        10,
        _latin1(f"Business Plan — {project.nom}"),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        6,
        _latin1(f"Direction : {project.direction}"),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.multi_cell(
        0,
        6,
        _latin1(f"Durée estimée : {project.duree_estimee_mois} mois"),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(4)

    for index, (title, content) in enumerate(business_plan.sections.items(), start=1):
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, _latin1(f"{index}. {title}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(
            0,
            6,
            _latin1(_strip_markdown(content)),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(2)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, _latin1("Note de synthèse CODIR"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        6,
        _latin1(_strip_markdown(business_plan.synthese_codir)),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    return bytes(pdf.output())


def _strip_markdown(text: str) -> str:
    """Retire les marqueurs Markdown simples pour un rendu PDF lisible."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return text


def _latin1(text: str) -> str:
    """Replie le texte sur l'encodage latin-1 supporté par les polices PDF."""
    return text.encode("latin-1", "replace").decode("latin-1")
