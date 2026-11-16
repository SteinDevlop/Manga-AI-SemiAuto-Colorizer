"""Alembic script template."""

${message}
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '${up_revision}'
down_revision = ${down_revision!r}
branch_labels = ${branch_labels!r}
depends_on = ${depends_on!r}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
