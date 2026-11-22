"""Persist mask review and correction metadata.

Revision ID: 0005_mask_corrections
Revises: 0004_users
"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005_mask_corrections"
down_revision: Union[str, None] = "0004_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("mask_artifacts", sa.Column("corregido", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("mask_artifacts", sa.Column("correcciones", sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column("mask_artifacts", "correcciones")
    op.drop_column("mask_artifacts", "corregido")
