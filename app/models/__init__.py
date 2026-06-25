"""Modèles de données (SQLAlchemy ORM).

Regroupe et expose les entités persistées afin que ``Base.metadata`` les
connaisse au moment de la création des tables.
"""

from __future__ import annotations

from app.models.project import (
    BusinessPlan,
    FinancialAssumption,
    FinancialHypothesis,
    FinancialImport,
    FinancialStatement,
    OpportunityType,
    Project,
    RiskType,
    Scenario,
    Score,
    StrategicAssessment,
    StrategicParameter,
)

__all__ = [
    "BusinessPlan",
    "FinancialAssumption",
    "FinancialHypothesis",
    "FinancialImport",
    "FinancialStatement",
    "OpportunityType",
    "Project",
    "RiskType",
    "Scenario",
    "Score",
    "StrategicAssessment",
    "StrategicParameter",
]
