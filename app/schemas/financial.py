"""Schémas Pydantic des hypothèses financières (US-1.2).

Données financières clés saisies par le porteur de projet et nécessaires à la
génération des scénarios financiers.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FinancialAssumptionCreate(BaseModel):
    """Hypothèses financières saisies pour un projet.

    Attributes:
        investissement_initial: Investissement initial en euros (>= 0).
        revenus_annuels: Revenus annuels attendus en euros (>= 0).
        couts_annuels: Coûts annuels d'exploitation en euros (>= 0).
        delai_rentabilite_mois: Délai estimé avant rentabilité, en mois (> 0).
    """

    investissement_initial: float = Field(ge=0, description="Investissement initial (€).")
    revenus_annuels: float = Field(ge=0, description="Revenus annuels attendus (€).")
    couts_annuels: float = Field(ge=0, description="Coûts annuels d'exploitation (€).")
    delai_rentabilite_mois: int = Field(gt=0, le=600, description="Délai avant rentabilité (mois).")


class FinancialAssumptionResponse(BaseModel):
    """Hypothèses financières persistées renvoyées par l'API.

    Attributes:
        id: Identifiant technique.
        project_id: Projet rattaché.
        investissement_initial: Investissement initial en euros.
        revenus_annuels: Revenus annuels attendus en euros.
        couts_annuels: Coûts annuels d'exploitation en euros.
        delai_rentabilite_mois: Délai avant rentabilité, en mois.
        created_at: Date de saisie (UTC).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    investissement_initial: float
    revenus_annuels: float
    couts_annuels: float
    delai_rentabilite_mois: int
    created_at: datetime
