"""Tests de la résilience des migrations au démarrage (BIZ-49)."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app import db


@pytest.fixture(autouse=True)
def _no_sleep() -> Iterator[None]:
    """Neutralise les délais d'attente pour des tests rapides."""
    with patch.object(db.time, "sleep", return_value=None):
        yield


def _operational_error() -> OperationalError:
    """Construit une ``OperationalError`` simulant un MySQL injoignable."""
    return OperationalError("SELECT 1", {}, Exception("timed out"))


def test_run_migrations_succeeds_first_try() -> None:
    """Une migration réussie n'effectue qu'une seule tentative."""
    upgrade = MagicMock()
    with (
        patch("alembic.command.upgrade", upgrade),
        patch("alembic.config.Config"),
    ):
        db.run_migrations()

    upgrade.assert_called_once()


def test_run_migrations_retries_then_succeeds() -> None:
    """La migration est retentée tant que la base est injoignable."""
    upgrade = MagicMock(side_effect=[_operational_error(), _operational_error(), None])
    with (
        patch("alembic.command.upgrade", upgrade),
        patch("alembic.config.Config"),
    ):
        db.run_migrations(max_attempts=5, delay_seconds=0.0)

    assert upgrade.call_count == 3


def test_run_migrations_raises_after_max_attempts() -> None:
    """La dernière erreur est propagée après épuisement des tentatives."""
    upgrade = MagicMock(side_effect=_operational_error())
    with (
        patch("alembic.command.upgrade", upgrade),
        patch("alembic.config.Config"),
        pytest.raises(OperationalError),
    ):
        db.run_migrations(max_attempts=3, delay_seconds=0.0)

    assert upgrade.call_count == 3
