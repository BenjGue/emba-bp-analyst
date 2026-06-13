"""Schémas Pydantic pour la création et la restitution d'un projet (US-1.1).

Définit les données d'entrée du formulaire de création (nom, description,
direction concernée, horizon temporel) et la représentation renvoyée par l'API
après persistance.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Direction(StrEnum):
    """Directions de La Poste éligibles au dépôt d'un projet.

    Liste fixe proposée au porteur de projet sous forme de menu déroulant.
    """

    SERVICES_COURRIER_COLIS = "Services-Courrier-Colis"
    LA_BANQUE_POSTALE = "La Banque Postale"
    LA_POSTE_GROUPE = "La Poste Groupe"
    RESEAU_LA_POSTE = "Réseau La Poste"
    GEOPOST = "Geopost"
    NUMERIQUE = "Numérique"


class ProjectCreate(BaseModel):
    """Informations générales saisies pour créer un projet.

    Attributes:
        nom: Nom du projet (obligatoire, 1 à 200 caractères).
        description: Description du projet (obligatoire, 1 à 1000 caractères).
        direction: Direction concernée (valeur de l'énumération ``Direction``).
        duree_estimee_mois: Horizon temporel estimé en mois (entier > 0).
    """

    nom: str = Field(min_length=1, max_length=200, description="Nom du projet.")
    description: str = Field(min_length=1, max_length=1000, description="Description du projet.")
    direction: Direction = Field(description="Direction concernée.")
    duree_estimee_mois: int = Field(
        gt=0, le=600, description="Durée estimée du projet, en mois (> 0)."
    )


class ProjectResponse(BaseModel):
    """Projet persisté renvoyé par l'API.

    Attributes:
        id: Identifiant technique du projet créé.
        nom: Nom du projet.
        description: Description du projet.
        direction: Direction concernée.
        duree_estimee_mois: Horizon temporel estimé en mois.
        created_at: Date de création (UTC).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identifiant technique du projet.")
    nom: str = Field(description="Nom du projet.")
    description: str = Field(description="Description du projet.")
    direction: Direction = Field(description="Direction concernée.")
    duree_estimee_mois: int = Field(description="Durée estimée en mois.")
    created_at: datetime = Field(description="Date de création (UTC).")
