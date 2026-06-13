"""Modèles ORM des projets et de leurs scores de pertinence.

Schéma minimal nécessaire à US-2.2 (persistance du score). Le modèle ``Project``
sera enrichi par US-1.1 (BIZ-7) ; il n'expose ici que les champs requis pour
rattacher un score à un projet.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    """Retourne l'horodatage UTC courant (timezone-aware)."""
    return datetime.now(UTC)


class Project(Base):
    """Projet soumis par un porteur de projet.

    Attributes:
        id: Identifiant technique du projet.
        name: Nom du projet.
        created_at: Date de création (UTC).
        scores: Scores de pertinence calculés pour ce projet.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    scores: Mapped[list[Score]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Score(Base):
    """Score de pertinence persisté pour un projet.

    Attributes:
        id: Identifiant technique du score.
        project_id: Référence vers le projet évalué.
        total: Score global (0-100).
        dimensions: Détail par dimension, sérialisé en JSON.
        created_at: Horodatage du calcul (UTC).
        project: Projet associé.
    """

    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    total: Mapped[float]
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="scores")
