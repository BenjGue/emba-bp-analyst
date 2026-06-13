"""Modèles de données (SQLAlchemy ORM).

Regroupe et expose les entités persistées afin que ``Base.metadata`` les
connaisse au moment de la création des tables.
"""

from __future__ import annotations

from app.models.project import Project, Score

__all__ = ["Project", "Score"]
