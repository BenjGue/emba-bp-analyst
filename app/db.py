"""Couche d'accès à la base de données (SQLAlchemy 2.0).

Centralise la création du moteur, la fabrique de sessions et la dépendance
FastAPI ``get_db``. Le moteur est construit paresseusement à partir de
``Settings.database_url`` et mis en cache pour toute la durée du processus.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    """Classe de base déclarative commune à tous les modèles ORM."""


@lru_cache
def get_engine() -> Engine:
    """Construit (une seule fois) le moteur SQLAlchemy depuis la configuration.

    Pour SQLite, un ``StaticPool`` et ``check_same_thread=False`` sont utilisés
    afin de partager une connexion unique (indispensable pour une base en
    mémoire utilisée par les tests).

    Returns:
        Le moteur SQLAlchemy partagé.
    """
    url = get_settings().database_url
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    """Fournit une session de base de données par requête.

    Yields:
        Une session SQLAlchemy fermée automatiquement en fin de requête.
    """
    session = Session(get_engine())
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Crée les tables manquantes à partir des modèles enregistrés."""
    from app import models  # noqa: F401  (enregistre les tables sur ``Base``)

    Base.metadata.create_all(bind=get_engine())
