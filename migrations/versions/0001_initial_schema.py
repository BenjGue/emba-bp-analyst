"""Schéma initial : projets, finances, scores, business plans, scénarios, imports.

Cette migration matérialise l'ensemble du schéma relationnel décrit par les
modèles SQLAlchemy (``app/models/project.py``) et le DDL de référence
(``db/schema.sql``). Elle constitue le point de départ versionné de la base
(BIZ-29) et remplace l'approche ``create_all`` en production.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-15

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiants de révision Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Taille maximale (octets) d'un import financier : oriente MySQL vers MEDIUMBLOB.
_MAX_IMPORT_BYTES = 5_000_000


def upgrade() -> None:
    """Crée l'ensemble des tables du schéma applicatif."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("direction", sa.String(length=100), nullable=False),
        sa.Column("duree_estimee_mois", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "financial_assumptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("investissement_initial", sa.Float(), nullable=False),
        sa.Column("revenus_annuels", sa.Float(), nullable=False),
        sa.Column("couts_annuels", sa.Float(), nullable=False),
        sa.Column("delai_rentabilite_mois", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )

    op.create_table(
        "strategic_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("rentabilite", sa.Integer(), nullable=False),
        sa.Column("alignement", sa.Integer(), nullable=False),
        sa.Column("risque", sa.Integer(), nullable=False),
        sa.Column("impact_operationnel", sa.Integer(), nullable=False),
        sa.Column("impact_social", sa.Integer(), nullable=False),
        sa.Column("faisabilite", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "business_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("synthese_codir", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )

    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "financial_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(length=_MAX_IMPORT_BYTES), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )


def downgrade() -> None:
    """Supprime l'ensemble des tables du schéma applicatif."""
    op.drop_table("financial_imports")
    op.drop_table("scenarios")
    op.drop_table("business_plans")
    op.drop_table("scores")
    op.drop_table("strategic_assessments")
    op.drop_table("financial_assumptions")
    op.drop_table("projects")
