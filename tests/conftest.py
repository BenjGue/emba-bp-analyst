"""Fixtures partagées des tests.

Force une base SQLite en mémoire pour isoler les tests de toute base réelle,
réinitialise les caches de configuration/moteur et fournit un client HTTP ainsi
qu'un projet de test persisté.
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite://"  # base en mémoire, avant tout import app

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import Base, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Project  # noqa: E402
from app.services.ai import AiCompletion  # noqa: E402


class FakeAiClient:
    """Faux client IA pour les tests : aucun appel réseau.

    La réponse est produite par une fonction injectée qui inspecte les prompts,
    ce qui permet de simuler chaque agent (analyste, financier, ...) selon le
    contenu du prompt système. Tous les appels sont enregistrés pour assertion.

    Attributes:
        responder: Fonction ``(system, user) -> texte`` simulant le modèle.
        calls: Historique des appels reçus.
    """

    def __init__(self, responder: Callable[[str, str], str]) -> None:
        """Initialise le faux client.

        Args:
            responder: Fonction simulant la réponse du modèle.
        """
        self.responder = responder
        self.calls: list[dict[str, object]] = []

    def complete(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> AiCompletion:
        """Simule un appel au modèle et restitue une réponse cannée.

        Args:
            system: Instruction système.
            user: Message utilisateur.
            json_mode: Indicateur de réponse JSON (enregistré, non utilisé).
            max_tokens: Plafond de jetons (enregistré, non utilisé).

        Returns:
            La complétion simulée.
        """
        self.calls.append({"system": system, "user": user, "json_mode": json_mode})
        return AiCompletion(text=self.responder(system, user), input_tokens=10, output_tokens=20)


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
        project = Project(
            nom="Projet Test",
            description="Projet de test pour les scénarios automatisés.",
            direction="Numérique",
            duree_estimee_mois=12,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project.id
