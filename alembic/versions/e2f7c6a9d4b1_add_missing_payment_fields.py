"""add_missing_payment_fields

Revision ID: e2f7c6a9d4b1
Revises: 9c1e7f4b2a08
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2f7c6a9d4b1"
down_revision: Union[str, Sequence[str], None] = "9c1e7f4b2a08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "payments",
        sa.Column("currency", sa.String(length=10), server_default="INR", nullable=False),
    )
    op.add_column(
        "payments",
        sa.Column("payment_method", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.alter_column("payments", "currency", server_default=None)
    op.create_index("idx_payments_provider_payment", "payments", ["provider_payment_id"], unique=False)
    op.create_index("idx_payments_user_status", "payments", ["user_id", "status"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_payments_user_status", table_name="payments")
    op.drop_index("idx_payments_provider_payment", table_name="payments")
    op.drop_column("payments", "failure_reason")
    op.drop_column("payments", "payment_method")
    op.drop_column("payments", "currency")
