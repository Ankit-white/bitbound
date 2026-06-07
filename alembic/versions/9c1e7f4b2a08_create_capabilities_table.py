"""create capabilities table

Revision ID: 9c1e7f4b2a08
Revises: 8b4d2a6f13c9
Create Date: 2026-06-07 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1e7f4b2a08"
down_revision: Union[str, Sequence[str], None] = "8b4d2a6f13c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "capabilities",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("credit_cost", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_capabilities_active", "capabilities", ["is_active"], unique=False)
    op.create_index("idx_capabilities_category", "capabilities", ["category"], unique=False)
    op.create_index("idx_capabilities_name", "capabilities", ["name"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_capabilities_name", table_name="capabilities")
    op.drop_index("idx_capabilities_category", table_name="capabilities")
    op.drop_index("idx_capabilities_active", table_name="capabilities")
    op.drop_table("capabilities")
