"""Add character_memory table for stable character memory.

Revision ID: 0002_character_memory
Revises: 0001_initial_schema
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_character_memory"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "character_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding", sa.String(), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("atributos_estables", sa.JSON(), nullable=True),
        sa.Column("atributos_escena", sa.JSON(), nullable=True),
        sa.Column("referencia_estable", sa.String(length=512), nullable=True),
        sa.Column("pagina_origen_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pagina_origen_id"],
            ["pages.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_character_memory_character_id"),
        "character_memory",
        ["character_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_character_memory_pagina_origen_id"),
        "character_memory",
        ["pagina_origen_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("character_memory")
