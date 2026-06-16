"""Modèles ORM des projets, hypothèses, scores et business plans.

Schéma relationnel normalisé (US-5.1) : un ``Project`` agrège ses hypothèses
financières (US-1.2), son évaluation stratégique (US-1.3), ses scores (US-2.x),
son business plan généré (US-3.x / US-4.1) et ses scénarios financiers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, LargeBinary, String, Text
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
        financial_assumption: Hypothèses financières saisies (0 ou 1).
        strategic_assessment: Évaluation stratégique saisie (0 ou 1).
        business_plan: Business plan généré (0 ou 1).
        scenarios: Scénarios financiers générés.
        financial_import: Fichier Excel financier importé (0 ou 1).
        financial_statement: Tableau financier multi-colonnes importé (0 ou 1).
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
        order_by="Score.created_at",
    )
    financial_assumption: Mapped[FinancialAssumption | None] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    strategic_assessment: Mapped[StrategicAssessment | None] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    business_plan: Mapped[BusinessPlan | None] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    scenarios: Mapped[list[Scenario]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    financial_import: Mapped[FinancialImport | None] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    financial_statement: Mapped[FinancialStatement | None] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
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


class FinancialAssumption(Base):
    """Hypothèses financières clés d'un projet (US-1.2).

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché (unique).
        investissement_initial: Investissement initial, en euros.
        revenus_annuels: Revenus annuels attendus, en euros.
        couts_annuels: Coûts annuels d'exploitation, en euros.
        delai_rentabilite_mois: Délai estimé avant rentabilité, en mois.
        created_at: Horodatage de saisie (UTC).
        project: Projet associé.
    """

    __tablename__ = "financial_assumptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True)
    investissement_initial: Mapped[float]
    revenus_annuels: Mapped[float]
    couts_annuels: Mapped[float]
    delai_rentabilite_mois: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="financial_assumption")


class StrategicAssessment(Base):
    """Évaluation stratégique d'un projet sur 6 dimensions (US-1.3).

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché (unique).
        rentabilite: Note de rentabilité (0-10).
        alignement: Note d'alignement stratégique (0-10).
        risque: Note de maîtrise du risque (0-10).
        impact_operationnel: Note d'impact opérationnel (0-10).
        impact_social: Note d'impact social/environnemental (0-10).
        faisabilite: Note de faisabilité technique (0-10).
        ai_synthese: Synthèse de la logique de l'IA ayant proposé les notes
            (BIZ-56), conservée pour l'audit.
        user_justification: Justification d'une modification manuelle des notes
            proposées par l'IA (BIZ-56).
        created_at: Horodatage de saisie (UTC).
        project: Projet associé.
    """

    __tablename__ = "strategic_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True)
    rentabilite: Mapped[int]
    alignement: Mapped[int]
    risque: Mapped[int]
    impact_operationnel: Mapped[int]
    impact_social: Mapped[int]
    faisabilite: Mapped[int]
    ai_synthese: Mapped[str | None] = mapped_column(Text, default=None)
    user_justification: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="strategic_assessment")


class BusinessPlan(Base):
    """Business plan généré pour un projet (US-3.x / US-4.1).

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché (unique).
        status: Statut de génération (``generated``).
        sections: Sections du BP sérialisées en JSON (titre -> contenu).
        synthese_codir: Note de synthèse pour le comité de direction.
        created_at: Horodatage de génération (UTC).
        project: Projet associé.
    """

    __tablename__ = "business_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="generated")
    sections: Mapped[dict[str, Any]] = mapped_column(JSON)
    synthese_codir: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="business_plan")


class Scenario(Base):
    """Scénario financier généré (bas / médian / haut).

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché.
        type: Type de scénario (``bas``, ``median``, ``haut``).
        data: Données chiffrées du scénario, sérialisées en JSON.
        created_at: Horodatage de génération (UTC).
        project: Projet associé.
    """

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    type: Mapped[str] = mapped_column(String(20))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="scenarios")


# Taille maximale (octets) de blob acceptée : oriente MySQL vers MEDIUMBLOB.
_MAX_IMPORT_BYTES = 5_000_000


class FinancialImport(Base):
    """Fichier Excel de données financières importé pour un projet (BIZ-36).

    Le fichier d'origine est conservé (audit / re-téléchargement) en plus des
    valeurs extraites, qui alimentent les hypothèses financières du projet.

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché (unique : le dernier import remplace le précédent).
        filename: Nom du fichier d'origine.
        content_type: Type MIME déclaré à l'upload.
        size_bytes: Taille du fichier, en octets.
        content: Contenu binaire du fichier Excel.
        uploaded_at: Horodatage de l'import (UTC).
        project: Projet associé.
    """

    __tablename__ = "financial_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column()
    content: Mapped[bytes] = mapped_column(LargeBinary(length=_MAX_IMPORT_BYTES))
    uploaded_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="financial_import")


class FinancialStatement(Base):
    """Tableau financier multi-colonnes importé depuis Excel (BIZ-32).

    Matérialise le format détaillé décrit dans la spécification (Projet2.docx) :
    le temps en lignes (semaines/mois/années) et les catégories en colonnes
    (dépenses, recettes, agrégats). Les séries chronologiques sont conservées
    telles quelles ; les hypothèses financières scalaires du projet en sont
    dérivées de façon déterministe.

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché (unique : le dernier import remplace le précédent).
        period_unit: Granularité temporelle détectée (``semaine`` / ``mois`` / ``annee``).
        periods: Libellés des périodes (axe temporel), dans l'ordre.
        depenses: Séries de dépenses par poste (clé canonique -> valeurs par période).
        recettes: Séries de recettes par poste.
        agregats: Séries d'agrégats (marge brute, EBE, résultat d'exploitation, EBITDA).
        created_at: Horodatage de l'import (UTC).
        project: Projet associé.
    """

    __tablename__ = "financial_statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True)
    period_unit: Mapped[str] = mapped_column(String(20))
    periods: Mapped[list[Any]] = mapped_column(JSON)
    depenses: Mapped[dict[str, Any]] = mapped_column(JSON)
    recettes: Mapped[dict[str, Any]] = mapped_column(JSON)
    agregats: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="financial_statement")
