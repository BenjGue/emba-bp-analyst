"""Configuration applicative chargée depuis l'environnement.

Toutes les variables sensibles (clés API, chaînes de connexion) sont lues via
``pydantic-settings`` depuis les variables d'environnement ou un fichier
``.env.local`` (jamais commité).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de configuration de l'application.

    Attributes:
        app_name: Nom lisible de l'application, exposé par l'API.
        environment: Environnement d'exécution (``dev``, ``staging``, ``prod``).
        debug: Active le mode debug (logs verbeux, rechargement).
        database_url: Chaîne de connexion SQLAlchemy à la base de données.
    """

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "BizPlan-IA"
    environment: str = "dev"
    debug: bool = False
    database_url: str = "sqlite:///./bizplan.db"


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance unique de configuration (mise en cache).

    L'usage de ``lru_cache`` garantit qu'un seul objet ``Settings`` est
    instancié pour toute la durée de vie du processus, évitant des relectures
    inutiles de l'environnement.

    Returns:
        L'instance de configuration partagée.
    """
    return Settings()
