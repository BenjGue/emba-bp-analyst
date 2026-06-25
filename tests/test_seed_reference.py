"""Tests du seed des catalogues de référence (BIZ-88).

Vérifie la volumétrie minimale exigée par le cahier des charges et
l'idempotence du seed (catalogues partagés exploités par l'IA).
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import (
    FinancialHypothesis,
    OpportunityType,
    RiskType,
    StrategicParameter,
)
from scripts.seed import seed_reference_data


def _count(session: Session, model: type) -> int:
    """Retourne le nombre de lignes d'un catalogue de référence."""
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def test_seed_reference_respecte_les_volumes_minimaux(client: TestClient) -> None:
    """Le seed atteint les volumes exigés (BIZ-88)."""
    with Session(get_engine()) as session:
        seed_reference_data(session)
        assert _count(session, RiskType) >= 10
        assert _count(session, OpportunityType) >= 10
        assert _count(session, StrategicParameter) >= 20
        assert 30 <= _count(session, FinancialHypothesis) <= 50


def test_seed_reference_est_idempotent(client: TestClient) -> None:
    """Un second appel ne crée aucun doublon (BIZ-88)."""
    with Session(get_engine()) as session:
        first = seed_reference_data(session)
        assert sum(first.values()) > 0
        second = seed_reference_data(session)
        assert sum(second.values()) == 0


def test_seed_reference_couvre_les_six_dimensions(client: TestClient) -> None:
    """Les paramètres stratégiques couvrent les six dimensions de scoring (BIZ-88)."""
    with Session(get_engine()) as session:
        seed_reference_data(session)
        dimensions = {row[0] for row in session.execute(select(StrategicParameter.dimension)).all()}
    assert dimensions == {
        "rentabilite",
        "alignement",
        "risque",
        "impact_operationnel",
        "impact_social",
        "faisabilite",
    }
