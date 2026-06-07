"""set email verified default false

Revision ID: 8b4d2a6f13c9
Revises: 5d3e8f1a9c27
Create Date: 2026-06-07 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b4d2a6f13c9"
down_revision: Union[str, Sequence[str], None] = "5d3e8f1a9c27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "email_verified",
        server_default=sa.false(),
        existing_type=sa.Boolean(),
        existing_nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "email_verified",
        server_default=sa.true(),
        existing_type=sa.Boolean(),
        existing_nullable=False
    )
