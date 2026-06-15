"""Environnement d'exécution Alembic (BIZ-29).

Ce module configure les migrations en réutilisant la source de vérité de
l'application :

* l'URL de connexion provient de :func:`app.config.get_settings` (aucun secret
  en dur, même base que l'application : SQLite en dev, MySQL en prod) ;
* les métadonnées cibles proviennent de :data:`app.db.Base` (l'import de
  ``app.models`` enregistre toutes les tables ORM), ce qui permet
  l'autogénération (``alembic revision --autogenerate``).
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  # enregistre toutes les tables sur Base.metadata
from app.config import get_settings
from app.db import Base

# Objet de configuration Alembic donnant accès aux valeurs du fichier .ini.
config = context.config

# Initialise le logging Python à partir du fichier de configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées cibles pour l'autogénération des migrations.
target_metadata = Base.metadata


def _database_url() -> str:
    """Retourne l'URL de connexion lue depuis la configuration applicative.

    Returns:
        L'URL SQLAlchemy (SQLite en dev, MySQL en prod via Key Vault).
    """
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Exécute les migrations en mode « offline » (génération de SQL)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode « online » (connexion réelle)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
