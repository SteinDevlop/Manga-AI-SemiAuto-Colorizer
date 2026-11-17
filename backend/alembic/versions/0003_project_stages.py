"""Add stage tracking fields to projects.

Revision ID: 0003_project_stages
Revises: 0002_character_memory
Create Date: 2026-11-17

Adds ``current_stage``, ``status``, ``stage_progress`` and ``cover_image`` to
the ``projects`` table and backfills existing rows with coherent defaults
(current_stage="upload", status="en_progreso", empty stage progress).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_project_stages"
down_revision: Union[str, None] = "0002_character_memory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("current_stage", sa.String(), nullable=False, server_default="upload"),
    )
    op.add_column(
        "projects",
        sa.Column("status", sa.String(), nullable=False, server_default="en_progreso"),
    )
    op.add_column(
        "projects",
        sa.Column("stage_progress", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "projects",
        sa.Column("cover_image", sa.String(), nullable=True),
    )

    # Backfill existing rows with coherent defaults (S22).
    op.execute(
        "UPDATE projects SET current_stage = 'upload', status = 'en_progreso', "
        "stage_progress = '[]' WHERE current_stage IS NULL OR status IS NULL"
    )


def downgrade() -> None:
    op.drop_column("projects", "cover_image")
    op.drop_column("projects", "stage_progress")
    op.drop_column("projects", "status")
    op.drop_column("projects", "current_stage")
