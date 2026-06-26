"""Tables de référence : risques, opportunités, paramètres, hypothèses (BIZ-88).

Ajoute les catalogues de référence partagés (indépendants des projets) exigés
par le cahier des charges (Projet2.docx) : ``risk_types``, ``opportunity_types``,
``strategic_parameters`` et ``financial_hypotheses``. Ces tables alimentent
l'analyse comparative des projets par l'IA.

Revision ID: 0004_reference_catalogs
Revises: 0003_strategic_ai_audit
Create Date: 2026-06-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiants de révision Alembic.
revision: str = "0004_reference_catalogs"
down_revision: str | None = "0003_strategic_ai_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée les quatre tables de référence du catalogue (BIZ-88)."""
    op.create_table(
        "risk_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("libelle", sa.String(length=150), nullable=False),
        sa.Column("categorie", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("severite_defaut", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "opportunity_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("libelle", sa.String(length=150), nullable=False),
        sa.Column("categorie", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("impact_defaut", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "strategic_parameters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("libelle", sa.String(length=150), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("poids", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "financial_hypotheses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("libelle", sa.String(length=150), nullable=False),
        sa.Column("categorie", sa.String(length=50), nullable=False),
        sa.Column("unite", sa.String(length=20), nullable=False),
        sa.Column("valeur_defaut", sa.Float(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )


def downgrade() -> None:
    """Supprime les quatre tables de référence du catalogue (BIZ-88)."""
    op.drop_table("financial_hypotheses")
    op.drop_table("strategic_parameters")
    op.drop_table("opportunity_types")
    op.drop_table("risk_types")
