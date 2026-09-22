"""expenses module

Revision ID: 20260922_007
Revises: 20260922_006
Create Date: 2026-09-22 23:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_007"
down_revision: Union[str, None] = "20260922_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.add_column(sa.Column("expense_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("payment_method", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("recurrence_months", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("recurring_key", sa.String(length=120), nullable=True))
        batch_op.create_index("ix_expenses_expense_date", ["expense_date"], unique=False)
        batch_op.create_index("ix_expenses_payment_method", ["payment_method"], unique=False)
        batch_op.create_index("ix_expenses_recurring_key", ["recurring_key"], unique=False)

    op.execute("UPDATE expenses SET expense_date = COALESCE(due_date, DATE('now')) WHERE expense_date IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_index("ix_expenses_recurring_key")
        batch_op.drop_index("ix_expenses_payment_method")
        batch_op.drop_index("ix_expenses_expense_date")
        batch_op.drop_column("recurring_key")
        batch_op.drop_column("recurrence_months")
        batch_op.drop_column("is_recurring")
        batch_op.drop_column("payment_method")
        batch_op.drop_column("expense_date")
