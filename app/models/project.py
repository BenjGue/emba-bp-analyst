"""Modèles ORM des projets et de leurs scores de pertinence.

Le modèle ``Project`` porte les informations générales saisies par le porteur
de projet (US-1.1) ; le modèle ``Score`` persiste les scores calculés (US-2.2).
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
        nom: Nom du projet.
        description: Description du projet.
        direction: Direction concernée.
        duree_estimee_mois: Horizon temporel estimé, en mois.
        created_at: Date de création (UTC).
        scores: Scores de pertinence calculés pour ce projet.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000))
    direction: Mapped[str] = mapped_column(String(100))
    duree_estimee_mois: Mapped[int] = mapped_column()
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
