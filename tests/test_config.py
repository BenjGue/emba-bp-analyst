"""Tests de la configuration applicative."""

from __future__ import annotations

from app.config import Settings, get_settings


def test_get_settings_is_cached() -> None:
    """``get_settings`` retourne toujours la même instance (cache LRU)."""
    assert get_settings() is get_settings()


def test_default_settings_values() -> None:
    """Les valeurs par défaut de configuration sont correctes."""
    settings = Settings()

    assert settings.app_name == "BizPlan-IA"
    assert settings.environment == "dev"
    assert settings.debug is False
