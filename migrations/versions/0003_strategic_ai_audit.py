"""Colonnes d'audit IA sur strategic_assessments (BIZ-56).

Ajoute deux colonnes facultatives à la table des évaluations stratégiques :
``ai_synthese`` (synthèse de la logique de l'IA ayant proposé les notes) et
``user_justification`` (justification d'une modification manuelle des notes).

Revision ID: 0003_strategic_ai_audit
Revises: 0002_financial_statements
Create Date: 2026-06-16

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiants de révision Alembic.
revision: str = "0003_strategic_ai_audit"
down_revision: str | None = "0002_financial_statements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Ajoute les colonnes d'audit IA à ``strategic_assessments``."""
    op.add_column(
        "strategic_assessments",
        sa.Column("ai_synthese", sa.Text(), nullable=True),
    )
    op.add_column(
        "strategic_assessments",
        sa.Column("user_justification", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Supprime les colonnes d'audit IA de ``strategic_assessments``."""
    op.drop_column("strategic_assessments", "user_justification")
    op.drop_column("strategic_assessments", "ai_synthese")
