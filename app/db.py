"""Couche d'accès à la base de données (SQLAlchemy 2.0).

Centralise la création du moteur, la fabrique de sessions et la dépendance
FastAPI ``get_db``. Le moteur est construit paresseusement à partir de
``Settings.database_url`` et mis en cache pour toute la durée du processus.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings

logger = logging.getLogger(__name__)

# Racine du dépôt : permet de localiser ``alembic.ini`` et ``migrations/``.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


def run_migrations(max_attempts: int = 12, delay_seconds: float = 5.0) -> None:
    """Applique les migrations Alembic jusqu'à la dernière révision (``head``).

    Utilisé en production (MySQL) pour faire évoluer le schéma de façon
    versionnée et auditable, plutôt que par ``create_all``. L'opération est
    idempotente : si la base est déjà à jour, aucune modification n'est faite.

    La base MySQL Flexible (tier Burstable) s'arrête automatiquement après une
    période d'inactivité et met plusieurs dizaines de secondes à redémarrer.
    Pour éviter qu'un démarrage à froid ne fasse planter le conteneur en
    boucle, la migration est tentée plusieurs fois avec un délai fixe entre
    chaque essai (BIZ-49).

    Args:
        max_attempts: Nombre maximal de tentatives avant d'abandonner.
        delay_seconds: Délai d'attente, en secondes, entre deux tentatives.

    Raises:
        OperationalError: Si la base reste injoignable après toutes les
            tentatives.
    """
    from alembic import command
    from alembic.config import Config

    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_PROJECT_ROOT / "migrations"))

    last_error: OperationalError | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            command.upgrade(config, "head")
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "Base de données injoignable (tentative %d/%d) : %s",
                attempt,
                max_attempts,
                exc,
            )
            if attempt < max_attempts:
                time.sleep(delay_seconds)

    assert last_error is not None  # noqa: S101 (garanti par la boucle ci-dessus)
    logger.error("Échec des migrations après %d tentatives.", max_attempts)
    raise last_error
