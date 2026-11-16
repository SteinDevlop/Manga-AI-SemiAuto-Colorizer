"""Initial schema for Manga Colorizer domain entities.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-15

Creates tables: projects, pages, panels, analyses, characters,
character_appearances, character_attributes, character_palettes,
mask_artifacts, colorization_jobs, model_manifests.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre_archivo_original", sa.String(), nullable=False),
        sa.Column("hash_sha256", sa.String(), nullable=False),
        sa.Column("ruta_archivo", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("ancho", sa.Integer(), nullable=True),
        sa.Column("alto", sa.Integer(), nullable=True),
        sa.Column("tamano_bytes", sa.BigInteger(), nullable=True),
        sa.Column("estado", sa.String(), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash_sha256"),
    )
    op.create_index(
        op.f("ix_pages_project_id"),
        "pages",
        ["project_id"],
        unique=False,
    )

    op.create_table(
        "panels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("numero_orden", sa.Integer(), nullable=False),
        sa.Column("x", sa.Float(), nullable=True),
        sa.Column("y", sa.Float(), nullable=True),
        sa.Column("ancho", sa.Float(), nullable=True),
        sa.Column("alto", sa.Float(), nullable=True),
        sa.Column("confianza_deteccion", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_panels_page_id"),
        "panels",
        ["page_id"],
        unique=False,
    )

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default="analysis_pending"),
        sa.Column("confianza_global", sa.Float(), nullable=True),
        sa.Column("version_modelo", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_analyses_page_id"),
        "analyses",
        ["page_id"],
        unique=True,
    )

    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("confianza_identidad", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "character_appearances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("panel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confianza_deteccion", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["panel_id"],
            ["panels.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_character_appearances_page_id"),
        "character_appearances",
        ["page_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_character_appearances_character_id"),
        "character_appearances",
        ["character_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_character_appearances_panel_id"),
        "character_appearances",
        ["panel_id"],
        unique=False,
    )

    op.create_table(
        "character_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre_atributo", sa.String(), nullable=False),
        sa.Column("valor_sugerido", sa.String(), nullable=True),
        sa.Column("valor_aprobado", sa.String(), nullable=True),
        sa.Column("confianza_sugerencia", sa.Float(), nullable=True),
        sa.Column("esta_aprobado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_character_attributes_character_id"),
        "character_attributes",
        ["character_id"],
        unique=False,
    )

    op.create_table(
        "character_palettes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre_color", sa.String(), nullable=False),
        sa.Column("valor_hex", sa.String(), nullable=True),
        sa.Column("esta_aprobado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_character_palettes_character_id"),
        "character_palettes",
        ["character_id"],
        unique=False,
    )

    op.create_table(
        "mask_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("appearance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_mascara", sa.String(), nullable=False),
        sa.Column("ruta_archivo", sa.String(), nullable=False),
        sa.Column("hash_sha256", sa.String(), nullable=False),
        sa.Column("ancho", sa.Integer(), nullable=True),
        sa.Column("alto", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["appearance_id"],
            ["character_appearances.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mask_artifacts_appearance_id"),
        "mask_artifacts",
        ["appearance_id"],
        unique=False,
    )

    op.create_table(
        "colorization_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default="pending"),
        sa.Column("progreso", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mensaje", sa.String(), nullable=True),
        sa.Column("ruta_resultado", sa.String(), nullable=True),
        sa.Column("version_modelo", sa.String(), nullable=True),
        sa.Column("parametros", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_colorization_jobs_analysis_id"),
        "colorization_jobs",
        ["analysis_id"],
        unique=False,
    )

    op.create_table(
        "model_manifests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre_modelo", sa.String(), nullable=False),
        sa.Column("familia", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("hash_pesos", sa.String(), nullable=True),
        sa.Column("licencia", sa.String(), nullable=True),
        sa.Column("fuente", sa.String(), nullable=True),
        sa.Column("capacidades", sa.JSON(), nullable=True),
        sa.Column("requisitos_hardware", sa.JSON(), nullable=True),
        sa.Column("estado", sa.String(), nullable=False, server_default="disponible"),
        sa.Column("parametros_soportados", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("model_manifests")
    op.drop_table("colorization_jobs")
    op.drop_table("mask_artifacts")
    op.drop_table("character_palettes")
    op.drop_table("character_attributes")
    op.drop_table("character_appearances")
    op.drop_table("characters")
    op.drop_table("analyses")
    op.drop_table("panels")
    op.drop_table("pages")
    op.drop_table("projects")
