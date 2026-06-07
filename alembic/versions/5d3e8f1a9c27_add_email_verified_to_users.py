"""add email verified to users

Revision ID: 5d3e8f1a9c27
Revises: 4ba419ed068b
Create Date: 2026-06-07 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d3e8f1a9c27"
down_revision: Union[str, Sequence[str], None] = "4ba419ed068b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "email_verified")
