"""Schémas Pydantic du business plan généré (US-3.x / US-4.1).

Représentation du business plan structuré en sections et de la note de synthèse
CODIR, telle que renvoyée par l'API pour consultation.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScenarioResponse(BaseModel):
    """Scénario financier (bas / médian / haut).

    Attributes:
        type: Type de scénario (``bas``, ``median``, ``haut``).
        data: Données chiffrées du scénario.
    """

    model_config = ConfigDict(from_attributes=True)

    type: str
    data: dict[str, float]


class BusinessPlanResponse(BaseModel):
    """Business plan généré renvoyé par l'API.

    Attributes:
        project_id: Projet rattaché.
        status: Statut de génération.
        sections: Sections du BP (titre -> contenu Markdown).
        synthese_codir: Note de synthèse pour le comité de direction.
        scenarios: Scénarios financiers associés.
        created_at: Date de génération (UTC).
    """

    project_id: int
    status: str
    sections: dict[str, str] = Field(description="Sections du BP (titre -> contenu).")
    synthese_codir: str
    scenarios: list[ScenarioResponse] = Field(default_factory=list)
    created_at: datetime
