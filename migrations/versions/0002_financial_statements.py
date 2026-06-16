"""Table financial_statements : import Excel multi-colonnes (BIZ-32).

Ajoute la table des tableaux financiers détaillés (temps en lignes, catégories
en colonnes) importés depuis Excel, en complément de l'import simplifié
(``financial_imports``, BIZ-36).

Revision ID: 0002_financial_statements
Revises: 0001_initial_schema
Create Date: 2026-06-16

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiants de révision Alembic.
revision: str = "0002_financial_statements"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée la table des tableaux financiers détaillés."""
    op.create_table(
        "financial_statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("period_unit", sa.String(length=20), nullable=False),
        sa.Column("periods", sa.JSON(), nullable=False),
        sa.Column("depenses", sa.JSON(), nullable=False),
        sa.Column("recettes", sa.JSON(), nullable=False),
        sa.Column("agregats", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )


def downgrade() -> None:
    """Supprime la table des tableaux financiers détaillés."""
    op.drop_table("financial_statements")
