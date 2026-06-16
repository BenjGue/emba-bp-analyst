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
        ai_enabled: Active les appels réels au modèle IA (EPIC 3). Désactivé par
            défaut afin que les tests et la CI restent hors-ligne et
            déterministes ; la génération retombe alors sur le mode template.
        ai_endpoint: Endpoint Azure AI Foundry (ex. ``https://xxx.cognitiveservices.azure.com``).
        ai_deployment: Nom du déploiement de modèle à interroger (agnostique :
            Claude Sonnet, GPT, etc.). Le contrat ``chat/completions`` est commun.
        ai_api_version: Version d'API de l'inférence Azure.
        ai_api_key: Clé d'API du service Foundry. **Jamais en dur** : lue depuis
            l'environnement (dev) ou Key Vault (prod). Vide par défaut.
        ai_use_entra_id: Authentifie les appels via Entra ID (identité managée)
            plutôt qu'avec une clé API. Requis lorsque la ressource a
            ``disableLocalAuth=true`` (aucun secret à stocker).
        ai_timeout_s: Délai maximal (secondes) d'un appel au modèle.
        ai_max_tokens: Plafond de jetons générés par appel.
        ai_use_max_completion_tokens: Utilise le paramètre ``max_completion_tokens``
            (modèles GPT-5 et suivants) au lieu de ``max_tokens`` (modèles antérieurs).
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

    # --- Intégration IA (EPIC 3) ---------------------------------------------
    ai_enabled: bool = False
    ai_endpoint: str = ""
    ai_deployment: str = ""
    ai_api_version: str = "2024-10-21"
    ai_api_key: str = ""
    ai_use_entra_id: bool = False
    ai_timeout_s: float = 60.0
    ai_max_tokens: int = 2000
    ai_use_max_completion_tokens: bool = True


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
