"""Fixtures partagées des tests.

Force une base SQLite en mémoire pour isoler les tests de toute base réelle,
réinitialise les caches de configuration/moteur et fournit un client HTTP ainsi
qu'un projet de test persisté.
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite://"  # base en mémoire, avant tout import app

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import Base, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Project  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fournit un client de test HTTP sur une base en mémoire fraîche.

    Yields:
        Un ``TestClient`` configuré sur une instance fraîche de l'application.
    """
    get_settings.cache_clear()
    get_engine.cache_clear()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    get_engine.cache_clear()


@pytest.fixture
def project_id(client: TestClient) -> int:
    """Crée un projet de test et retourne son identifiant.

    Args:
        client: Fixture client garantissant l'initialisation de la base.

    Returns:
        L'identifiant du projet persisté.
    """
    with Session(get_engine()) as session:
        project = Project(name="Projet Test")
        session.add(project)
        session.commit()
        session.refresh(project)
        return project.id
