"""Fixtures partagées des tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fournit un client de test HTTP pour l'application FastAPI.

    Yields:
        Un ``TestClient`` configuré sur une instance fraîche de l'application.
    """
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
