"""support game versions 16_21 and 16_22

Revision ID: b7615a746ecb
Revises: bb1896e2e8fb
Create Date: 2026-11-16 20:31:02.950541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7615a746ecb'
down_revision: Union[str, Sequence[str], None] = 'bb1896e2e8fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Labels are the `schemas.GameVersion` member *names* (`_16_21`), not their
    # values (`16_21`); SQLAlchemy stores `.name` for native enums. `BEFORE`
    # keeps the type's declaration order newest-first, matching the enum.
    op.execute(
        sa.text("ALTER TYPE gameversion ADD VALUE IF NOT EXISTS '_16_21' BEFORE '_16_20'")
    )
    op.execute(
        sa.text("ALTER TYPE gameversion ADD VALUE IF NOT EXISTS '_16_22' BEFORE '_16_21'")
    )
    # Re-applied from `bb1896e2e8fb`, where it never landed: that revision is
    # stamped as applied but `queuetype` has no `swiftplay` label.
    op.execute(sa.text("ALTER TYPE queuetype ADD VALUE IF NOT EXISTS 'swiftplay'"))


def downgrade() -> None:
    """Downgrade schema."""
    # intentionally nothing here: enum labels can't be dropped
    pass
