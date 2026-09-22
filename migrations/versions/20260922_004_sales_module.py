"""sales module

Revision ID: 20260922_004
Revises: 20260922_003
Create Date: 2026-09-22 21:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_004"
down_revision: Union[str, None] = "20260922_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sales") as batch_op:
        batch_op.add_column(sa.Column("payment_status", sa.String(length=32), nullable=False, server_default="pending"))
        batch_op.add_column(sa.Column("channel", sa.String(length=32), nullable=False, server_default="other"))
        batch_op.add_column(sa.Column("payment_method", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("subtotal_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("total_cost", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("gross_profit", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.create_index("ix_sales_payment_status", ["payment_status"], unique=False)
        batch_op.create_index("ix_sales_channel", ["channel"], unique=False)
        batch_op.create_index("ix_sales_payment_method", ["payment_method"], unique=False)

    with op.batch_alter_table("sale_items") as batch_op:
        batch_op.add_column(sa.Column("product_name", sa.String(length=160), nullable=False, server_default="Produto"))
        batch_op.add_column(sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("total_cost", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("gross_profit", sa.Numeric(12, 2), nullable=False, server_default="0"))

    op.create_table(
        "sale_payments",
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(length=32), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sale_payments_id", "sale_payments", ["id"], unique=False)
    op.create_index("ix_sale_payments_payment_method", "sale_payments", ["payment_method"], unique=False)
    op.create_index("ix_sale_payments_paid_at", "sale_payments", ["paid_at"], unique=False)
    op.create_index("ix_sale_payments_sale_paid_at", "sale_payments", ["sale_id", "paid_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sale_payments_sale_paid_at", table_name="sale_payments")
    op.drop_index("ix_sale_payments_paid_at", table_name="sale_payments")
    op.drop_index("ix_sale_payments_payment_method", table_name="sale_payments")
    op.drop_index("ix_sale_payments_id", table_name="sale_payments")
    op.drop_table("sale_payments")

    with op.batch_alter_table("sale_items") as batch_op:
        batch_op.drop_column("gross_profit")
        batch_op.drop_column("total_cost")
        batch_op.drop_column("unit_cost")
        batch_op.drop_column("discount_amount")
        batch_op.drop_column("product_name")

    with op.batch_alter_table("sales") as batch_op:
        batch_op.drop_index("ix_sales_payment_method")
        batch_op.drop_index("ix_sales_channel")
        batch_op.drop_index("ix_sales_payment_status")
        batch_op.drop_column("amount_paid")
        batch_op.drop_column("gross_profit")
        batch_op.drop_column("total_cost")
        batch_op.drop_column("discount_amount")
        batch_op.drop_column("subtotal_amount")
        batch_op.drop_column("payment_method")
        batch_op.drop_column("channel")
        batch_op.drop_column("payment_status")
