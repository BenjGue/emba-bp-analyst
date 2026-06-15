"""Tests des migrations Alembic (BIZ-29).

Vérifie que les migrations versionnées sont cohérentes (révision unique) et
qu'appliquer ``alembic upgrade head`` puis ``downgrade base`` produit
exactement le schéma décrit par les modèles SQLAlchemy.
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

import app.models  # noqa: F401  (enregistre les tables sur Base.metadata)
from app.config import get_settings
from app.db import Base, run_migrations

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    """Construit une configuration Alembic pointant sur le dépôt.

    Returns:
        La configuration Alembic prête à l'emploi.
    """
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_PROJECT_ROOT / "migrations"))
    return config


def test_migrations_have_single_head() -> None:
    """L'historique des migrations ne doit comporter qu'une seule tête."""
    script = ScriptDirectory.from_config(_alembic_config())
    assert len(script.get_heads()) == 1


def test_upgrade_creates_all_model_tables(tmp_path, monkeypatch) -> None:
    """``upgrade head`` crée toutes les tables déclarées par les modèles."""
    db_path = tmp_path / "migration_test.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()

    command.upgrade(_alembic_config(), "head")

    engine = sa.create_engine(url)
    try:
        actual_tables = set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()
    get_settings.cache_clear()

    expected_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables)


def test_downgrade_removes_all_tables(tmp_path, monkeypatch) -> None:
    """``downgrade base`` supprime l'ensemble des tables applicatives."""
    db_path = tmp_path / "migration_downgrade.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()

    config = _alembic_config()
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = sa.create_engine(url)
    try:
        remaining = set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()
    get_settings.cache_clear()

    assert not (set(Base.metadata.tables.keys()) & remaining)


def test_run_migrations_applies_head(tmp_path, monkeypatch) -> None:
    """``run_migrations`` (helper applicatif) amène la base à la dernière révision."""
    db_path = tmp_path / "run_migrations.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()

    run_migrations()

    engine = sa.create_engine(url)
    try:
        tables = set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()
    get_settings.cache_clear()

    assert "alembic_version" in tables
    assert set(Base.metadata.tables.keys()).issubset(tables)
