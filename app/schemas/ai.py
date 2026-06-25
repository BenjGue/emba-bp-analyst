"""Schémas Pydantic de la couche IA (EPIC 3).

Définit les contrats d'entrée/sortie des fonctionnalités assistées par IA :
rédaction de description (BIZ-37) et sorties structurées des agents de
génération (BIZ-15 à BIZ-18). Ces schémas matérialisent le garde-fou « l'IA
propose, le backend valide ».
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.project import Direction


class DescriptionDraftRequest(BaseModel):
    """Idées clés fournies par le porteur pour générer une description (BIZ-37).

    Attributes:
        idees: Grandes idées du projet, en texte libre (1 à 2000 caractères).
        direction: Direction concernée, pour contextualiser la rédaction.
        nom: Nom éventuel du projet, utilisé comme contexte (facultatif).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    idees: str = Field(min_length=1, max_length=2000, description="Idées clés du projet.")
    direction: Direction = Field(description="Direction concernée.")
    nom: str | None = Field(default=None, max_length=200, description="Nom du projet (option).")


class DescriptionDraftResponse(BaseModel):
    """Description rédigée par l'IA (BIZ-37).

    Attributes:
        description: Description générée, bornée à 1000 caractères (limite de
            ``ProjectCreate.description``).
    """

    description: str = Field(description="Description rédigée par l'IA.")


class EvaluateurOutput(BaseModel):
    """Sortie structurée de l'agent Évaluateur (BIZ-56).

    L'IA propose les 6 notes stratégiques à partir des données du projet. Les
    notes sont ensuite bornées et validées côté backend (« l'IA propose, le
    backend valide »).

    Attributes:
        rentabilite: Note proposée de rentabilité (0-10).
        alignement: Note proposée d'alignement stratégique (0-10).
        risque: Note proposée de maîtrise du risque (0-10).
        impact_operationnel: Note proposée d'impact opérationnel (0-10).
        impact_social: Note proposée d'impact social/environnemental (0-10).
        faisabilite: Note proposée de faisabilité technique (0-10).
        justifications: Justification courte par dimension.
        synthese: Synthèse globale expliquant la logique d'évaluation.
    """

    rentabilite: int = Field(default=5, description="Note proposée de rentabilité (0-10).")
    alignement: int = Field(default=5, description="Note proposée d'alignement (0-10).")
    risque: int = Field(default=5, description="Note proposée de maîtrise du risque (0-10).")
    impact_operationnel: int = Field(default=5, description="Note proposée d'impact op. (0-10).")
    impact_social: int = Field(default=5, description="Note proposée d'impact social (0-10).")
    faisabilite: int = Field(default=5, description="Note proposée de faisabilité (0-10).")
    justifications: dict[str, str] = Field(
        default_factory=dict, description="Justification courte par dimension."
    )
    synthese: str = Field(default="", description="Synthèse globale expliquant les notes.")


class AnalysteOutput(BaseModel):
    """Sortie structurée de l'agent Analyste (BIZ-15).

    Attributes:
        forces: Forces identifiées du projet.
        faiblesses: Faiblesses identifiées.
        risques: Risques principaux.
        opportunites: Opportunités à saisir.
    """

    forces: list[str] = Field(default_factory=list, description="Forces du projet.")
    faiblesses: list[str] = Field(default_factory=list, description="Faiblesses du projet.")
    risques: list[str] = Field(default_factory=list, description="Risques principaux.")
    opportunites: list[str] = Field(default_factory=list, description="Opportunités.")


class FinancierOutput(BaseModel):
    """Commentaire qualitatif de l'agent Financier (BIZ-16).

    Les chiffres ne sont pas produits par l'IA : ils restent calculés par le
    backend. L'agent se limite à un commentaire narratif.

    Attributes:
        analyse_globale: Lecture d'ensemble des scénarios.
        scenario_bas: Commentaire du scénario bas.
        scenario_median: Commentaire du scénario médian.
        scenario_haut: Commentaire du scénario haut.
    """

    analyse_globale: str = Field(default="", description="Analyse globale.")
    scenario_bas: str = Field(default="", description="Commentaire scénario bas.")
    scenario_median: str = Field(default="", description="Commentaire scénario médian.")
    scenario_haut: str = Field(default="", description="Commentaire scénario haut.")


class RedacteurOutput(BaseModel):
    """Sections rédactionnelles du business plan (BIZ-17).

    Attributes:
        resume_executif: Résumé exécutif.
        presentation_projet: Présentation du projet.
        analyse_marche: Analyse du marché et du contexte.
        analyse_concurrentielle: Analyse concurrentielle.
        proposition_valeur: Proposition de valeur.
        modele_economique: Modèle économique.
        plan_operationnel: Plan opérationnel.
        analyse_risques: Analyse des risques.
        hypotheses_financieres: Hypothèses et scénarios financiers.
        impact_strategique: Impact stratégique et RSE.
        recommandation: Recommandation et prochaines étapes.
    """

    resume_executif: str = Field(default="", description="Résumé exécutif.")
    presentation_projet: str = Field(default="", description="Présentation du projet.")
    analyse_marche: str = Field(default="", description="Analyse du marché.")
    analyse_concurrentielle: str = Field(default="", description="Analyse concurrentielle.")
    proposition_valeur: str = Field(default="", description="Proposition de valeur.")
    modele_economique: str = Field(default="", description="Modèle économique.")
    plan_operationnel: str = Field(default="", description="Plan opérationnel.")
    analyse_risques: str = Field(default="", description="Analyse des risques.")
    hypotheses_financieres: str = Field(default="", description="Hypothèses financières.")
    impact_strategique: str = Field(default="", description="Impact stratégique et RSE.")
    recommandation: str = Field(default="", description="Recommandation.")


class SyntheseOutput(BaseModel):
    """Note de synthèse CODIR produite par l'agent Synthèse (BIZ-18).

    Attributes:
        synthese_codir: Texte de la note de synthèse (une page).
    """

    synthese_codir: str = Field(default="", description="Note de synthèse CODIR.")
