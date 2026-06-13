"""Schémas Pydantic pour le score de pertinence (US-2.1).

Définit les dimensions stratégiques en entrée et la structure détaillée du
score en sortie. Toutes les notes sont des entiers bornés ``[0, 10]`` validés
côté API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StrategicDimensions(BaseModel):
    """Notes stratégiques saisies par le porteur de projet (0 à 10).

    Chaque dimension est évaluée sur une échelle entière de 0 (très faible) à
    10 (excellent). Pour la dimension ``risque``, la note représente la
    **maîtrise du risque** : plus elle est élevée, plus le risque est maîtrisé.

    Attributes:
        rentabilite: Potentiel de rentabilité du projet.
        alignement: Alignement avec la stratégie de l'organisation.
        risque: Niveau de maîtrise du risque (10 = risque le mieux maîtrisé).
        impact_operationnel: Impact opérationnel attendu.
        impact_social: Impact social et environnemental.
        faisabilite: Faisabilité technique de la mise en œuvre.
    """

    rentabilite: int = Field(ge=0, le=10, description="Potentiel de rentabilité (0-10).")
    alignement: int = Field(ge=0, le=10, description="Alignement stratégique (0-10).")
    risque: int = Field(ge=0, le=10, description="Maîtrise du risque (0-10).")
    impact_operationnel: int = Field(ge=0, le=10, description="Impact opérationnel (0-10).")
    impact_social: int = Field(ge=0, le=10, description="Impact social/environnemental (0-10).")
    faisabilite: int = Field(ge=0, le=10, description="Faisabilité technique (0-10).")


class DimensionDetail(BaseModel):
    """Détail de la contribution d'une dimension au score global.

    Attributes:
        note: Note brute saisie (0 à 10).
        poids: Pondération appliquée à la dimension (somme des poids = 1.0).
        contribution: Contribution de la dimension au score final (0 à 100).
    """

    note: int = Field(ge=0, le=10, description="Note brute (0-10).")
    poids: float = Field(ge=0, le=1, description="Pondération appliquée (0-1).")
    contribution: float = Field(ge=0, le=100, description="Contribution au score (0-100).")


class ScoreResponse(BaseModel):
    """Résultat du calcul de score de pertinence.

    Attributes:
        total: Score global borné ``[0, 100]``, arrondi à 2 décimales.
        dimensions: Détail par dimension (note brute, poids, contribution).
    """

    total: float = Field(ge=0, le=100, description="Score global de pertinence (0-100).")
    dimensions: dict[str, DimensionDetail] = Field(
        description="Détail de la contribution de chaque dimension."
    )
